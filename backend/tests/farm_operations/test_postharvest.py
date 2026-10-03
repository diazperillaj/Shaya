"""
Beneficio, secado, calidad y salida a inventario: balance de masas entre
etapas, cierre del secado en una sola transacción con el inventario,
composición de las mezclas y trazabilidad en ambos sentidos.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.api.api_v1.inventory.service import ParchmentService
from app.core.exceptions.domain import ConflictError
from app.farm_operations.models import QualityEval
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.parchment import Parchment
from app.models.product import Product, ProductTypeEnum
from tests.farm_operations.payloads import API


@pytest.fixture
def farm(client, login, make_farmer, create_farm):
    _, user = make_farmer()
    login(user)
    return create_farm(altitude="1650")


@pytest.fixture
def make_harvest(client, farm, create_plot, create_cycle):
    """Cosecha en un lote nuevo de la finca; con `total`, ya cerrada."""

    def _make_harvest(plot_name: str, variety: str = "Castillo", total: str | None = None) -> dict:
        plot = create_plot(farm["id"], name=plot_name, variety=variety)
        cycle = create_cycle(plot["id"])
        harvest = client.post(f"{API}/harvests/create", json={"crop_cycle_id": cycle["id"], "start_date": "2025-04-01"}).json()
        if total is not None:
            closed = client.post(f"{API}/harvests/{harvest['id']}/close", json={"end_date": "2025-04-20", "total_cherry_kg": total})
            assert closed.status_code == 200, closed.text
            harvest = closed.json()
        return harvest

    return _make_harvest


@pytest.fixture
def parchment_product(db_session):
    """Producto que el inventario usa para todo pergamino."""
    product = Product(name="Sin tipo", quantity=0, type=ProductTypeEnum.other, active=True, generates_inventory=False)
    db_session.add(product)
    db_session.flush()
    return product


def new_wet(client, farm_id, inputs, **fields):
    return client.post(f"{API}/wet-processings/create", json={"farm_id": farm_id, "inputs": inputs, **fields})


def completed_wet(client, farm_id, inputs, washed_kg) -> dict:
    wet = new_wet(client, farm_id, inputs)
    assert wet.status_code == 200, wet.text
    response = client.post(f"{API}/wet-processings/{wet.json()['id']}/complete", json={"washed_kg": washed_kg})
    assert response.status_code == 200, response.text
    return response.json()


def new_drying(client, farm_id, inputs, **fields):
    body = {"farm_id": farm_id, "method": "marquesina", "start_date": "2025-04-21", "inputs": inputs, **fields}
    return client.post(f"{API}/dryings/create", json=body)


def complete_drying(client, drying_id, **fields):
    body = {
        "end_date": "2025-05-05", "final_humidity_pct": "11.2", "output_kg": "19",
        "destination": "stored", **fields,
    }
    return client.post(f"{API}/dryings/{drying_id}/complete", json=body)


def count(db_session, model) -> int:
    return db_session.query(model).count()


# ── Balance de masas: cosechas → beneficio ───────────────────────────────


def test_closed_harvest_total_caps_its_processing(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="300")
    new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "180"}])

    before = client.get(f"{API}/wet-processings/get").json()
    exceeded = new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "150"}])

    assert exceeded.status_code == 409
    assert "quedan 120 kg" in exceeded.json()["detail"]
    assert client.get(f"{API}/wet-processings/get").json() == before, "sin cambios en la base"
    assert new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "120"}]).status_code == 200


def test_open_harvest_is_processed_and_its_total_checked_at_close(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto")
    new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "90"}])
    url = f"{API}/harvests/{harvest['id']}/close"

    too_low = client.post(url, json={"end_date": "2025-04-20", "total_cherry_kg": "80"})
    assert too_low.status_code == 409
    assert "Ya se benefició 90 kg" in too_low.json()["detail"]

    closed = client.post(url, json={"end_date": "2025-04-20"})
    assert closed.json()["total_cherry_kg"] == "90.000", "sin recolección registrada, el total es lo beneficiado"
    assert closed.json()["kg_processed"] == "90.000"


def test_harvest_splits_among_several_processings(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="300")
    for cherry_kg in ("100", "120", "80"):
        assert new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": cherry_kg}]).status_code == 200

    trace = client.get(f"{API}/traceability/harvests/{harvest['id']}").json()
    assert trace["processed_kg"] == "300.000"
    assert [item["cherry_kg"] for item in trace["destinations"]] == ["100.000", "120.000", "80.000"]


def test_processing_mixes_harvests_of_its_farm_only(client, farm, make_harvest, create_farm, create_plot, create_cycle):
    local = make_harvest("Lote Alto", total="100")
    other_plot = create_plot(create_farm(name="Otra finca")["id"])
    other_cycle = create_cycle(other_plot["id"])
    foreign = client.post(f"{API}/harvests/create", json={"crop_cycle_id": other_cycle["id"]}).json()

    response = new_wet(client, farm["id"], [
        {"harvest_id": local["id"], "cherry_kg": "50"}, {"harvest_id": foreign["id"], "cherry_kg": "50"},
    ])

    assert response.status_code == 409


def test_replacing_inputs_rechecks_the_balance(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="100")
    wet = new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "60"}]).json()
    url = f"{API}/wet-processings/{wet['id']}/inputs"

    assert client.put(url, json={"inputs": [{"harvest_id": harvest["id"], "cherry_kg": "100"}]}).status_code == 200
    assert client.put(url, json={"inputs": [{"harvest_id": harvest["id"], "cherry_kg": "101"}]}).status_code == 409


# ── Beneficio ────────────────────────────────────────────────────────────


def test_stages_are_recorded_and_fermentation_hours_calculated(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="100")
    wet = new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}]).json()

    updated = client.put(f"{API}/wet-processings/update/{wet['id']}", json={
        "floats_kg": "3.5", "pulped_at": "2025-04-21T17:00:00-05:00",
        "fermentation_start": "2025-04-21T18:00:00-05:00", "fermentation_end": "2025-04-22T10:30:00-05:00",
        "fermentation_method": "tank", "fermentation_decided_by": "Don Arturo", "wash_count": 3,
    })

    assert updated.status_code == 200, updated.text
    assert (updated.json()["fermentation_hours"], updated.json()["cherry_kg"]) == ("16.5", "100.000")


@pytest.mark.parametrize(
    "fields, problem",
    [
        ({"fermentation_end": "2025-04-22T10:00:00-05:00"}, "cuándo empezó"),
        ({"fermentation_start": "2025-04-22T10:00:00-05:00", "fermentation_end": "2025-04-21T10:00:00-05:00"}, "antes de empezar"),
        ({"fermentation_method": "other"}, "cuál método"),
        ({"pulped_at": "2999-01-01T00:00:00-05:00"}, "no puede ser futura"),
    ],
)
def test_invalid_stages_are_rejected(client, farm, make_harvest, fields, problem):
    harvest = make_harvest("Lote Alto", total="100")

    response = new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}], **fields)

    assert response.status_code == 422
    assert problem in " ".join(error["msg"] for error in response.json()["detail"])


def test_washed_coffee_does_not_exceed_the_cherry(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="100")
    wet = new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}]).json()
    url = f"{API}/wet-processings/{wet['id']}/complete"

    assert client.post(url, json={}).status_code == 409, "exige el café lavado"
    assert client.post(url, json={"washed_kg": "101"}).status_code == 409
    completed = client.post(url, json={"washed_kg": "42"}).json()
    assert (completed["status"], completed["washed_kg"]) == ("completed", "42.000")
    assert client.put(f"{API}/wet-processings/update/{wet['id']}", json={}).status_code == 409, "completado = fijo"


# ── Balance de masas: beneficio → secado ─────────────────────────────────


def test_only_completed_processings_are_dried_within_their_washed_coffee(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="200")
    in_progress = new_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}]).json()
    assert new_drying(client, farm["id"], [{"wet_processing_id": in_progress["id"], "wet_kg": "10"}]).status_code == 409

    wet = completed_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}], "40")
    new_drying(client, farm["id"], [{"wet_processing_id": wet["id"], "wet_kg": "30"}])
    exceeded = new_drying(client, farm["id"], [{"wet_processing_id": wet["id"], "wet_kg": "15"}])

    assert exceeded.status_code == 409
    assert "quedan 10 kg" in exceeded.json()["detail"]


def test_dried_processing_is_frozen(client, farm, make_harvest):
    harvest = make_harvest("Lote Alto", total="100")
    wet = completed_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}], "40")
    new_drying(client, farm["id"], [{"wet_processing_id": wet["id"], "wet_kg": "40"}])

    assert client.post(f"{API}/wet-processings/{wet['id']}/reopen").status_code == 409
    assert client.delete(f"{API}/wet-processings/delete/{wet['id']}").status_code == 409


# ── Cierre del secado ────────────────────────────────────────────────────


@pytest.fixture
def drying(client, farm, make_harvest):
    """Secado de 40 kg de café lavado de 100 kg de cereza del Lote Alto."""
    harvest = make_harvest("Lote Alto", variety="Castillo", total="100")
    wet = completed_wet(client, farm["id"], [{"harvest_id": harvest["id"], "cherry_kg": "100"}], "40")
    response = new_drying(client, farm["id"], [{"wet_processing_id": wet["id"], "wet_kg": "40"}])
    assert response.status_code == 200, response.text
    return response.json()


def test_drying_closes_into_inventory_with_the_rule_of_three(client, db_session, farm, drying, parchment_product):
    closed = complete_drying(
        client, drying["id"], output_kg="19.3", destination="inventory",
        inventory_data={"full_price": "3200000", "purchase_date": "2025-05-06"},
    )

    assert closed.status_code == 200, closed.text
    body = closed.json()
    assert (body["status"], body["yield_pct"]) == ("completed", "19.3")
    parchment = db_session.get(Parchment, body["parchment_id"])
    assert parchment.drying_id == drying["id"]
    assert parchment.purchase_price == Decimal("494080.00"), "19,3 kg × $3.200.000 / 125"
    assert (parchment.full_price, parchment.initial_quantity, parchment.remaining_quantity) == (
        Decimal("3200000.00"), Decimal("19.300"), Decimal("19.300"),
    )
    assert (parchment.variety, parchment.humidity, parchment.altitude) == ("Castillo", Decimal("11.20"), Decimal("1650.00"))
    assert parchment.farmer_id == farm["farmer"]["id"]
    assert db_session.query(InventoryMovement).filter(InventoryMovement.parchment_id == parchment.id).count() == 1


def test_inventory_needs_its_price(client, drying):
    assert complete_drying(client, drying["id"], destination="inventory").status_code == 422


def test_failed_inventory_leaves_the_drying_open(client, db_session, drying, parchment_product, monkeypatch):
    def failing_create(self, data):
        self.db.add(Inventory(product_id=data.product_id, date=datetime.now(), quantity=data.initial_quantity))
        self.db.flush()
        raise ConflictError("Falla simulada del inventario")

    monkeypatch.setattr(ParchmentService, "create_parchment", failing_create)
    inventories = count(db_session, Inventory)

    response = complete_drying(
        client, drying["id"], destination="inventory", inventory_data={"full_price": "3200000"},
    )

    assert response.status_code == 409
    assert client.get(f"{API}/dryings/get/{drying['id']}").json()["status"] == "in_progress"
    assert count(db_session, Inventory) == inventories, "ni el secado se cerró ni quedó inventario a medias"


def test_without_parchment_product_nothing_changes(client, db_session, drying):
    response = complete_drying(client, drying["id"], destination="inventory", inventory_data={"full_price": "3200000"})

    assert response.status_code == 409
    assert client.get(f"{API}/dryings/get/{drying['id']}").json()["status"] == "in_progress"
    assert count(db_session, Parchment) == 0


def test_dry_parchment_does_not_exceed_the_washed_coffee(client, drying):
    assert complete_drying(client, drying["id"], output_kg="41").status_code == 409


def test_stored_parchment_goes_to_inventory_later(client, drying, parchment_product):
    complete_drying(client, drying["id"], destination="direct_sale")
    client.post(f"{API}/dryings/{drying['id']}/reopen")
    complete_drying(client, drying["id"], destination="stored", storage_place="Bodega")

    sent = client.post(f"{API}/dryings/{drying['id']}/to-inventory", json={"full_price": "3000000", "purchase_date": "2025-05-10"})

    assert sent.status_code == 200, sent.text
    assert (sent.json()["destination"], sent.json()["parchment_id"] is not None) == ("inventory", True)
    assert client.post(f"{API}/dryings/{drying['id']}/reopen").status_code == 409, "ya está en el inventario"
    assert client.post(f"{API}/dryings/{drying['id']}/to-inventory", json={"full_price": "1"}).status_code == 409


def test_humidity_checks_and_expected_range(client, drying):
    url = f"{API}/dryings/{drying['id']}/humidity-checks/create"
    client.post(url, json={"check_date": "2025-04-25", "humidity_pct": "30"})
    detail = client.post(url, json={"check_date": "2025-04-30", "humidity_pct": "18"}).json()

    assert [check["humidity_pct"] for check in detail["humidity_checks"]] == ["30.00", "18.00"]
    assert detail["humidity_range"] == ["10", "12"]
    assert client.post(url, json={"check_date": "2025-04-01", "humidity_pct": "40"}).status_code == 409
    assert complete_drying(client, drying["id"], end_date="2025-04-28").status_code == 409, "antes de la última medición"


# ── Composición y trazabilidad ───────────────────────────────────────────


def test_mix_composition_follows_the_kg(client, farm, make_harvest):
    alto = make_harvest("Lote Alto", variety="Castillo", total="300")
    bajo = make_harvest("Lote Bajo", variety="Cenicafé 1", total="200")
    wet_alto = completed_wet(client, farm["id"], [{"harvest_id": alto["id"], "cherry_kg": "300"}], "120")
    wet_bajo = completed_wet(client, farm["id"], [{"harvest_id": bajo["id"], "cherry_kg": "200"}], "80")

    # La mitad del café del Lote Alto y todo el del Lote Bajo
    drying = new_drying(client, farm["id"], [
        {"wet_processing_id": wet_alto["id"], "wet_kg": "60"}, {"wet_processing_id": wet_bajo["id"], "wet_kg": "80"},
    ]).json()

    assert drying["cherry_kg_traced"] == "350.000"
    assert [(plot["plot_name"], plot["cherry_kg"], plot["share_pct"]) for plot in drying["composition"]] == [
        ("Lote Bajo", "200.000", "57.1"), ("Lote Alto", "150.000", "42.9"),
    ]


def test_traceability_from_parchment_back_to_labors(client, farm, drying, parchment_product):
    closed = complete_drying(client, drying["id"], destination="inventory", inventory_data={"full_price": "3200000"}).json()
    cycle_id = closed["composition"][0]["harvests"][0]["crop_cycle_id"]
    client.post(f"{API}/flowering-records/create", json={
        "crop_cycle_id": cycle_id, "flowering_date": "2025-02-01", "intensity": "high",
    })

    trace = client.get(f"{API}/traceability/parchments/{closed['parchment_id']}")

    assert trace.status_code == 200, trace.text
    plot = trace.json()["plots"][0]
    assert (plot["plot_name"], plot["share_pct"]) == ("Lote Alto", "100.0")
    labors = {item["kind"]: item["count"] for item in plot["cycles"][0]["labors"]}
    assert labors["flowering-records"] == 1
    assert trace.json()["wet_processings"][0]["wet_kg"] == "40.000"


def test_harvest_traces_forward_to_its_parchment(client, farm, drying, parchment_product):
    closed = complete_drying(client, drying["id"], destination="inventory", inventory_data={"full_price": "3200000"}).json()
    harvest_id = closed["composition"][0]["harvests"][0]["harvest_id"]

    trace = client.get(f"{API}/traceability/harvests/{harvest_id}").json()

    destination = trace["destinations"][0]["dryings"][0]
    assert (destination["drying_id"], destination["cherry_kg"], destination["parchment_id"]) == (
        drying["id"], "100.000", closed["parchment_id"],
    )


def test_purchased_parchment_has_no_farm_trace(client, db_session, farm, parchment_product, make_farmer):
    farmer, _ = make_farmer("Proveedor")
    parchment = ParchmentService(db_session).create_parchment(type("Data", (), {
        "farmer_id": farmer.id, "product_id": parchment_product.id, "variety": None, "altitude": None,
        "humidity": None, "full_price": Decimal(3000000), "initial_quantity": Decimal(10),
        "purchase_date": datetime(2025, 5, 1).date(), "origin_batch": "LOTE-1", "observations": None,
        "drying_id": None,
    })())

    response = client.get(f"{API}/traceability/parchments/{parchment.id}")

    assert response.status_code == 404
    assert "comprado" in response.json()["detail"]


# ── Calidad ──────────────────────────────────────────────────────────────


def test_quality_by_stage(client, make_harvest, drying):
    harvest = make_harvest("Lote Medio", total="50")
    cherry = client.post(f"{API}/quality-evals/create", json={
        "stage": "cherry", "harvest_id": harvest["id"], "eval_date": "2025-04-10", "ripe_pct": "88", "green_pct": "7",
    })
    parchment = client.post(f"{API}/quality-evals/create", json={
        "stage": "parchment", "drying_id": drying["id"], "eval_date": "2025-05-05", "humidity_pct": "11", "score": "84.5",
    })

    assert (cherry.status_code, parchment.status_code) == (200, 200)
    listed = client.get(f"{API}/quality-evals/get", params={"harvest_id": harvest["id"]}).json()
    assert [item["ripe_pct"] for item in listed] == ["88.00"]


@pytest.mark.parametrize(
    "body, problem",
    [
        ({"stage": "cherry", "humidity_pct": "11"}, "no aplica"),
        ({"stage": "cherry"}, "al menos un resultado"),
        ({"stage": "parchment", "ripe_pct": "80"}, "es de un secado"),
        ({"stage": "cherry", "ripe_pct": "120"}, "less than or equal"),
    ],
)
def test_invalid_quality_evals_are_rejected(client, make_harvest, body, problem):
    harvest = make_harvest("Lote Medio", total="50")

    response = client.post(f"{API}/quality-evals/create", json={"harvest_id": harvest["id"], **body})

    assert response.status_code == 422
    assert problem in " ".join(error["msg"] for error in response.json()["detail"])


def test_database_checks_the_quality_stage(db_session, drying):
    db_session.add(QualityEval(stage="cherry", drying_id=drying["id"], eval_date=datetime(2025, 5, 1).date()))

    with pytest.raises(IntegrityError, match="ck_quality_evals_stage_ref"):
        db_session.flush()


# ── Alcance ──────────────────────────────────────────────────────────────


def test_postharvest_of_other_farmers_is_out_of_reach(client, login, make_farmer, drying):
    _, intruder = make_farmer("Otro")
    login(intruder)

    assert client.get(f"{API}/dryings/get").json() == []
    assert client.get(f"{API}/wet-processings/get").json() == []
    assert client.get(f"{API}/dryings/get/{drying['id']}").status_code == 404
    assert client.get(f"{API}/traceability/dryings/{drying['id']}").status_code == 404
    assert complete_drying(client, drying["id"]).status_code == 404
