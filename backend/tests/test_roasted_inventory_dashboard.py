"""
Tablero del inventario de maquilado (`GET /maquilado/dashboard`).

La línea de tiempo de cada producto debe cuadrar con su cantidad restante:
las ventas directas, las ferias y los movimientos salen de sus tablas, y la
venta consolidada de una feria cerrada no se cuenta dos veces.
"""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.models.customer import Customer
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.fair import Fair, FairStatusEnum
from app.models.fair_inventory import FairInventory
from app.models.farmer import Farmer
from app.models.inventory import Inventory
from app.models.parchment import Parchment
from app.models.person import Person
from app.models.process import Process
from app.models.product import Product, ProductTypeEnum
from app.models.roasted_coffe import RoastedCoffee
from app.models.roasted_movement import MovementDirectionEnum, RoastedMovement, RoastedMovementDetail
from app.models.sale import Sale, SaleStatusEnum

URL = "/api/v1/maquilado/dashboard"
UTC = timezone.utc


@pytest.fixture
def admin(make_user):
    return make_user("admin")


@pytest.fixture
def scenario(db_session, admin):
    """Un lote con tres productos y una salida de cada tipo."""
    db = db_session

    def product(name, kind=ProductTypeEnum.processed):
        p = Product(name=name, quantity=0, type=kind)
        db.add(p)
        return p

    parchment_product = product("Pergamino", ProductTypeEnum.parchment)
    ground = product("500g Molido")
    beans = product("250g Grano")
    small = product("125g Grano")

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
        remaining_quantity=Decimal("0"),
        purchase_date=date(2026, 4, 1),
    )
    db.add(parchment)
    db.flush()

    process = Process(
        invoice_number="F-100",
        process_date=date(2026, 5, 1),
        parchment_id=parchment.id,
        parchment_kg=Decimal("100"),
        resultant_kg=Decimal("80"),
        yield_percentage=Decimal("80"),
        subtotal=Decimal("0"),
        iva=Decimal("0"),
        total=Decimal("0"),
    )
    db.add(process)
    db.flush()

    lot = RoastedCoffee(process_id=process.id)
    db.add(lot)
    db.flush()

    # Restantes ya descontados, como los deja cada servicio
    ground_lot = DetailRoastedCoffee(roasted_coffee_id=lot.id, product_id=ground.id, quantity=10, remaining_quantity=4)
    beans_lot = DetailRoastedCoffee(roasted_coffee_id=lot.id, product_id=beans.id, quantity=5, remaining_quantity=2)
    small_lot = DetailRoastedCoffee(roasted_coffee_id=lot.id, product_id=small.id, quantity=6, remaining_quantity=6)
    db.add_all([ground_lot, beans_lot, small_lot])
    db.flush()

    def sale(sale_date, lines, customer=None):
        s = Sale(
            customer_id=customer.id if customer else None,
            user_id=admin.id,
            sale_date=sale_date,
            status=SaleStatusEnum.completed,
            subtotal=Decimal("0"),
            iva=Decimal("0"),
            total=Decimal("0"),
        )
        db.add(s)
        db.flush()
        for drc, qty in lines:
            db.add(DetailSale(
                sale_id=s.id,
                detail_roasted_coffee_id=drc.id,
                quantity=qty,
                unit_value=Decimal("0"),
                subtotal=Decimal("0"),
                iva=Decimal("0"),
                total=Decimal("0"),
            ))
        return s

    customer = Customer(customerType="Natural", city="Bogotá", person=Person(full_name="Carlos Cliente"))
    db.add(customer)
    db.flush()
    sale(date(2026, 5, 10), [(ground_lot, 3)], customer)

    # Feria cerrada: 4 asignadas, 3 vendidas, 1 devuelta. Empieza a las
    # 9 p. m. en Colombia: el día es el 14, no el 15 de UTC.
    closed_fair = Fair(
        name="Expo Café",
        location="Plaza",
        start_datetime=datetime(2026, 5, 15, 2, 0, tzinfo=UTC),
        status=FairStatusEnum.closed,
        user_id=admin.id,
    )
    db.add(closed_fair)
    db.flush()
    db.add(FairInventory(
        fair_id=closed_fair.id,
        detail_roasted_coffee_id=ground_lot.id,
        initial_quantity=4,
        remaining_quantity=1,
        unit_value=Decimal("0"),
    ))
    closed_fair.sale_id = sale(date(2026, 5, 16), [(ground_lot, 3)]).id

    open_fair = Fair(
        name="Mercado",
        start_datetime=datetime(2026, 6, 1, 15, 0, tzinfo=UTC),
        status=FairStatusEnum.open,
        user_id=admin.id,
    )
    db.add(open_fair)
    db.flush()
    db.add(FairInventory(
        fair_id=open_fair.id,
        detail_roasted_coffee_id=beans_lot.id,
        initial_quantity=1,
        remaining_quantity=1,
        unit_value=Decimal("0"),
    ))

    movement = RoastedMovement(movement_date=datetime(2026, 5, 20, 17, 0, tzinfo=UTC), observations="Envío a tienda")
    db.add(movement)
    db.flush()
    db.add_all([
        RoastedMovementDetail(
            movement_id=movement.id,
            detail_roasted_coffee_id=beans_lot.id,
            quantity=2,
            direction=MovementDirectionEnum.exit,
        ),
        RoastedMovementDetail(
            movement_id=movement.id,
            detail_roasted_coffee_id=small_lot.id,
            quantity=6,
            direction=MovementDirectionEnum.entry,
            created_lot=True,
        ),
    ])
    db.flush()

    return {"lot": lot, "ground": ground_lot, "beans": beans_lot, "small": small_lot}


def test_lot_carries_origin_and_totals(login, admin, scenario):
    response = login(admin).get(URL)

    assert response.status_code == 200
    [lot] = response.json()["lots"]
    assert lot["id"] == scenario["lot"].id
    assert lot["invoice_number"] == "F-100"
    assert lot["process_date"] == "2026-05-01"
    assert lot["variety"] == "Castillo"
    assert lot["farmer_name"] == "Ana Caficultora"
    assert lot["farm_name"] == "La Esperanza"
    assert lot["altitude"] == 1750

    totals = {p["name"]: (p["total_in"], p["total_out"], p["remaining_quantity"]) for p in lot["products"]}
    assert totals == {
        "500g Molido": (10, 6, 4),
        "250g Grano": (5, 3, 2),
        "125g Grano": (6, 0, 6),
    }


def test_events_reconcile_with_remaining_quantity(login, admin, scenario):
    events = login(admin).get(URL).json()["events"]

    def of(detail):
        return [(e["event_date"], e["kind"], e["quantity"]) for e in events if e["detail_id"] == detail.id]

    # La venta consolidada de la feria no aparece: sus 3 unidades son las de la feria
    assert of(scenario["ground"]) == [
        ("2026-05-01", "process", 10),
        ("2026-05-10", "sale", -3),
        ("2026-05-14", "fair", -3),
    ]
    # Feria abierta: lo asignado está fuera de bodega
    assert of(scenario["beans"]) == [
        ("2026-05-01", "process", 5),
        ("2026-05-20", "movement", -2),
        ("2026-06-01", "fair", -1),
    ]
    # Lote creado por un movimiento: su entrada es el movimiento, no el proceso
    assert of(scenario["small"]) == [("2026-05-20", "movement", 6)]

    for detail in ("ground", "beans", "small"):
        drc = scenario[detail]
        assert sum(q for _, _, q in of(drc)) == drc.remaining_quantity

    assert [e["event_date"] for e in events] == sorted(e["event_date"] for e in events)


def test_event_references(login, admin, scenario):
    events = login(admin).get(URL).json()["events"]
    by_kind = {(e["kind"], e["detail_id"]): e for e in events}

    sale = by_kind[("sale", scenario["ground"].id)]
    assert sale["reference"].startswith("Venta #")
    assert sale["note"] == "Carlos Cliente"
    assert by_kind[("fair", scenario["beans"].id)]["note"] == "En curso"
    assert by_kind[("movement", scenario["beans"].id)]["note"] == "Envío a tienda"
    assert by_kind[("process", scenario["ground"].id)]["reference"] == "Factura F-100"
