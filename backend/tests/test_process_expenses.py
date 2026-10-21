"""
Gastos de un proceso de maquila: son gastos generales con `process_id`.

Solo se asocian al crearse desde el detalle del proceso; desde la pestaña
Gastos no hay forma de asociarlos. Cualquier cambio a un gasto asociado,
venga de donde venga, recalcula el unit_cost de los lotes del proceso.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.api.api_v1.processes.cost_service import ProcessCostService
from app.models.detail_process import DetailProcess
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.expense_category import ExpenseCategory
from app.models.farmer import Farmer
from app.models.inventory import Inventory
from app.models.parchment import Parchment
from app.models.person import Person
from app.models.process import Process
from app.models.product import Product, ProductTypeEnum
from app.models.roasted_coffe import RoastedCoffee

GENERAL_URL = "/api/v1/general-expenses"
UTC = timezone.utc


@pytest.fixture
def admin(make_user):
    return make_user("admin")


@pytest.fixture
def staff(login, admin):
    return login(admin)


@pytest.fixture
def category(db_session):
    """Categoría que crea la migración al mover los gastos de proceso."""
    return db_session.query(ExpenseCategory).filter_by(name="Transporte").one()


@pytest.fixture
def scenario(db_session):
    """
    Proceso de 10 kg de un lote de 100 kg que costó 1.000.000, embolsado en
    40 bolsas de 250 g con maquila de 40.000: sin gastos, cada bolsa cuesta
    250 g × (100.000 / 10.000 g) + 40.000 / 40 = 3.500.
    """
    db = db_session
    parchment_product = Product(name="Pergamino", quantity=0, type=ProductTypeEnum.parchment)
    beans = Product(name="250g Grano", quantity=0, type=ProductTypeEnum.processed)
    db.add_all([parchment_product, beans])

    farmer = Farmer(
        farm_name="La Esperanza",
        village="Vereda",
        municipality="Municipio",
        person=Person(full_name="Ana Caficultora"),
    )
    db.add(farmer)
    db.flush()

    inventory = Inventory(product_id=parchment_product.id, date=datetime(2026, 4, 1, tzinfo=UTC), quantity=100)
    db.add(inventory)
    db.flush()
    parchment = Parchment(
        inventory_id=inventory.id,
        farmer_id=farmer.id,
        variety="Castillo",
        altitude=Decimal("1750"),
        purchase_price=Decimal("1000000"),
        full_price=Decimal("1000000"),
        initial_quantity=Decimal("100"),
        remaining_quantity=Decimal("90"),
        purchase_date=date(2026, 4, 1),
    )
    db.add(parchment)
    db.flush()

    process = Process(
        invoice_number="F-200",
        process_date=date(2026, 5, 1),
        parchment_id=parchment.id,
        parchment_kg=Decimal("10"),
        resultant_kg=Decimal("8"),
        yield_percentage=Decimal("80"),
        subtotal=Decimal("40000"),
        iva=Decimal("0"),
        total=Decimal("40000"),
    )
    db.add(process)
    db.flush()

    db.add(DetailProcess(
        process_id=process.id,
        date=date(2026, 5, 1),
        product_id=beans.id,
        bag_quantity=40,
        grams_per_bag=250,
        unit_value=Decimal("1000"),
        iva=Decimal("0"),
        total=Decimal("40000"),
    ))
    lot = RoastedCoffee(process_id=process.id)
    db.add(lot)
    db.flush()
    roasted = DetailRoastedCoffee(roasted_coffee_id=lot.id, product_id=beans.id, quantity=40, remaining_quantity=40)
    db.add(roasted)
    db.flush()

    ProcessCostService(db).recalculate_process_costs(process.id)
    return process, roasted


def expense_payload(category, amount=20000, **extra):
    return {
        "expense_date": "2026-05-02",
        "amount": amount,
        "category_id": category.id,
        "description": "Transporte a la tostadora",
        **extra,
    }


def unit_cost(db_session, roasted):
    db_session.refresh(roasted)
    return roasted.unit_cost


def test_expense_created_from_process_is_a_general_expense(staff, db_session, category, scenario):
    process, roasted = scenario
    assert unit_cost(db_session, roasted) == Decimal("3500.00")

    res = staff.post(f"/api/v1/process/{process.id}/expenses/create", json=expense_payload(category))

    assert res.status_code == 200
    created = res.json()
    assert created["process_id"] == process.id
    assert created["process"]["invoice_number"] == "F-200"

    listed = {e["id"]: e for e in staff.get(f"{GENERAL_URL}/get").json()}
    assert listed[created["id"]]["process_id"] == process.id

    # 20.000 más de costo de café: 250 g × (120.000 / 10.000 g) + 1.000
    assert unit_cost(db_session, roasted) == Decimal("4000.00")

    costs = staff.get(f"/api/v1/process/{process.id}/costs").json()
    assert Decimal(str(costs["process_expenses_total"])) == Decimal("20000")
    [expense] = costs["process_expenses"]
    assert expense["category"]["name"] == "Transporte"
    assert expense["description"] == "Transporte a la tostadora"


def test_expenses_tab_cannot_link_a_process(staff, db_session, category, scenario):
    process, roasted = scenario

    res = staff.post(f"{GENERAL_URL}/create", json=expense_payload(category, process_id=process.id))

    assert res.status_code == 200
    expense_id = res.json()["id"]
    assert res.json()["process_id"] is None

    res = staff.put(f"{GENERAL_URL}/update/{expense_id}", json=expense_payload(category, process_id=process.id))

    assert res.status_code == 200
    assert res.json()["process_id"] is None
    assert unit_cost(db_session, roasted) == Decimal("3500.00")


def test_editing_or_deleting_from_expenses_tab_recalculates_cost(staff, db_session, category, scenario):
    process, roasted = scenario
    expense_id = staff.post(
        f"/api/v1/process/{process.id}/expenses/create", json=expense_payload(category)
    ).json()["id"]

    res = staff.put(f"{GENERAL_URL}/update/{expense_id}", json={"amount": 40000})

    assert res.status_code == 200
    assert res.json()["process_id"] == process.id
    assert unit_cost(db_session, roasted) == Decimal("4500.00")

    assert staff.delete(f"{GENERAL_URL}/delete/{expense_id}").status_code == 200
    assert unit_cost(db_session, roasted) == Decimal("3500.00")


def test_process_with_expenses_cannot_be_deleted(staff, category, scenario):
    process, _ = scenario
    staff.post(f"/api/v1/process/{process.id}/expenses/create", json=expense_payload(category))

    res = staff.delete(f"/api/v1/process/delete/{process.id}")

    assert res.status_code == 409
    assert "1 gasto(s) del proceso" in res.json()["detail"]


def test_expense_for_unknown_process_is_rejected(staff, category):
    res = staff.post("/api/v1/process/999999/expenses/create", json=expense_payload(category))

    assert res.status_code == 404
