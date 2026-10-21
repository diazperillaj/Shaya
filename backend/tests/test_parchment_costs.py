"""
Precio del pergamino y costo por bolsa.

El precio del lote entra al costo de café de cada bolsa: al editar el precio
de la carga (`full_price`) de un pergamino, los procesos que lo consumieron
recalculan el unit_cost de sus lotes. Las demás ediciones no tocan costos.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.api.api_v1.processes.cost_service import ProcessCostService
from app.models.detail_process import DetailProcess
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.farmer import Farmer
from app.models.inventory import Inventory
from app.models.parchment import Parchment
from app.models.person import Person
from app.models.process import Process
from app.models.product import Product, ProductTypeEnum
from app.models.roasted_coffe import RoastedCoffee

URL = "/api/v1/inventory/update"
UTC = timezone.utc


@pytest.fixture
def admin(login, make_user):
    return login(make_user("admin"))


@pytest.fixture
def scenario(db_session):
    """
    Dos lotes de pergamino de 100 kg con la carga a 1.250.000 (el lote cuesta
    1.000.000). Cada uno alimenta un proceso de 10 kg embolsado en 40 bolsas
    de 250 g con maquila de 40.000: cada bolsa cuesta
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

    def lot_with_process(invoice):
        inventory = Inventory(product_id=parchment_product.id, date=datetime(2026, 4, 1, tzinfo=UTC), quantity=100)
        db.add(inventory)
        db.flush()
        parchment = Parchment(
            inventory_id=inventory.id,
            farmer_id=farmer.id,
            variety="Castillo",
            altitude=Decimal("1750"),
            purchase_price=Decimal("1000000"),
            full_price=Decimal("1250000"),
            initial_quantity=Decimal("100"),
            remaining_quantity=Decimal("90"),
            purchase_date=date(2026, 4, 1),
        )
        db.add(parchment)
        db.flush()

        process = Process(
            invoice_number=invoice,
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
        return parchment, roasted

    return lot_with_process("F-300"), lot_with_process("F-301")


def unit_cost(db_session, roasted):
    db_session.refresh(roasted)
    return roasted.unit_cost


def test_changing_lot_price_recalculates_its_processes(admin, db_session, scenario):
    (parchment, roasted), (_, other_roasted) = scenario
    assert unit_cost(db_session, roasted) == Decimal("3500.00")

    res = admin.put(f"{URL}/{parchment.id}", json={"full_price": 3000000})

    assert res.status_code == 200
    assert Decimal(str(res.json()["purchase_price"])) == Decimal("2400000")
    # El lote ahora costó 2.400.000: 250 g × (240.000 / 10.000 g) + 1.000
    assert unit_cost(db_session, roasted) == Decimal("7000.00")
    # El proceso del otro lote no cambia
    assert unit_cost(db_session, other_roasted) == Decimal("3500.00")


def test_other_edits_leave_costs_untouched(admin, db_session, scenario):
    (parchment, roasted), _ = scenario
    # Un costo distinto al de la fórmula delata cualquier recálculo
    roasted.unit_cost = Decimal("1234.00")
    db_session.flush()

    assert admin.put(f"{URL}/{parchment.id}", json={"variety": "Geisha"}).status_code == 200
    assert admin.put(f"{URL}/{parchment.id}", json={"full_price": 1250000}).status_code == 200

    assert unit_cost(db_session, roasted) == Decimal("1234.00")
