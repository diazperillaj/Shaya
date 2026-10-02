"""
Labores del ciclo: el mismo CRUD para las seis, fechas dentro del ciclo,
insumos activos y registro de una labor en varios lotes a la vez.
"""

import pytest

from tests.farm_operations.payloads import API


@pytest.fixture
def farmer(client, login, make_farmer):
    _, user = make_farmer()
    login(user)
    return user


@pytest.fixture
def farm(farmer, create_farm):
    return create_farm()


@pytest.fixture
def supply(farmer, create_supply):
    return create_supply()


@pytest.fixture
def cycle(farm, create_plot, create_cycle):
    return create_cycle(create_plot(farm["id"])["id"])


def payloads(supply_id: int) -> dict:
    """Cuerpo mínimo válido de cada labor (sin el ciclo)."""
    return {
        "fertilizations": {
            "supply_id": supply_id, "application_date": "2025-03-01", "method": "soil",
            "quantity": "120", "cost": "180000",
        },
        "phytosanitary-apps": {
            "supply_id": supply_id, "application_date": "2025-03-01", "target": "Broca", "quantity": "0.5",
        },
        "irrigations": {"irrigation_date": "2025-03-01", "duration_minutes": 90},
        "pest-monitorings": {"monitoring_date": "2025-03-01", "broca_pct": "2.5"},
        "cultural-practices": {"practice_type": "weeding", "practice_date": "2025-03-01", "cost": "60000"},
        "flowering-records": {"flowering_date": "2025-03-01", "intensity": "high"},
    }


DATE_FIELDS = {
    "fertilizations": "application_date",
    "phytosanitary-apps": "application_date",
    "irrigations": "irrigation_date",
    "pest-monitorings": "monitoring_date",
    "cultural-practices": "practice_date",
    "flowering-records": "flowering_date",
}
KINDS = list(DATE_FIELDS)


def create(client, kind, cycle_id, supply_id, **overrides):
    body = {**payloads(supply_id)[kind], "crop_cycle_id": cycle_id, **overrides}
    return client.post(f"{API}/{kind}/create", json=body)


# ── CRUD común ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("kind", KINDS)
def test_every_labor_is_recorded_corrected_and_deleted(client, cycle, supply, kind):
    created = create(client, kind, cycle["id"], supply["id"])
    assert created.status_code == 200, created.text
    record = created.json()
    assert (record["plot_id"], record["plot_name"], record["cycle_number"]) == (
        cycle["plot_id"], cycle["plot_name"], 1,
    )

    listed = client.get(f"{API}/{kind}/get", params={"plot_id": cycle["plot_id"]}).json()
    assert [item["id"] for item in listed] == [record["id"]]

    body = {**payloads(supply["id"])[kind], DATE_FIELDS[kind]: "2025-03-05"}
    updated = client.put(f"{API}/{kind}/update/{record['id']}", json=body)
    assert updated.status_code == 200, updated.text
    assert updated.json()[DATE_FIELDS[kind]] == "2025-03-05"

    assert client.delete(f"{API}/{kind}/delete/{record['id']}").status_code == 200
    assert client.get(f"{API}/{kind}/get", params={"crop_cycle_id": cycle["id"]}).json() == []


def test_supply_is_returned_with_its_unit(client, cycle, supply):
    record = create(client, "fertilizations", cycle["id"], supply["id"]).json()

    assert record["supply"] == {"id": supply["id"], "name": supply["name"], "unit": "kg"}


def test_list_filters_by_date_range(client, cycle, supply):
    for day in ("2025-02-01", "2025-03-01", "2025-04-01"):
        create(client, "irrigations", cycle["id"], supply["id"], irrigation_date=day)

    listed = client.get(f"{API}/irrigations/get", params={"date_from": "2025-02-15", "date_to": "2025-03-31"}).json()

    assert [item["irrigation_date"] for item in listed] == ["2025-03-01"]


# ── Fechas dentro del ciclo ──────────────────────────────────────────────


def test_labor_date_falls_inside_its_cycle(client, cycle, supply):
    before_start = create(client, "flowering-records", cycle["id"], supply["id"], flowering_date="2025-01-01")
    assert before_start.status_code == 409
    assert "anterior al inicio del ciclo 1" in before_start.json()["detail"]

    client.post(f"{API}/crop-cycles/{cycle['id']}/close", json={"end_date": "2025-06-30"})

    forgotten = create(client, "flowering-records", cycle["id"], supply["id"], flowering_date="2025-05-01")
    assert forgotten.status_code == 200, "un registro olvidado se completa después del cierre"
    after_end = create(client, "flowering-records", cycle["id"], supply["id"], flowering_date="2025-07-01")
    assert after_end.status_code == 409


def test_closed_plot_takes_no_new_labors(client, cycle, supply):
    client.post(f"{API}/crop-cycles/{cycle['id']}/close", json={"end_date": "2025-06-30"})
    client.post(f"{API}/plots/{cycle['plot_id']}/close", json={})

    response = create(client, "flowering-records", cycle["id"], supply["id"])

    assert response.status_code == 409
    assert "cerrado" in response.json()["detail"]


# ── Validaciones de cada labor ───────────────────────────────────────────


@pytest.mark.parametrize(
    "kind, overrides, problem",
    [
        ("cultural-practices", {"practice_type": "other"}, "Indica cuál labor es"),
        ("pest-monitorings", {"broca_pct": None}, "al menos un resultado"),
        ("pest-monitorings", {"other_pest_pct": "3"}, "cuál es la otra plaga"),
        ("pest-monitorings", {"broca_pct": "101"}, "less than or equal"),
        ("fertilizations", {"quantity": "0"}, "greater than 0"),
        ("flowering-records", {"flowering_date": "2999-01-01"}, "no puede ser futura"),
    ],
)
def test_invalid_labors_are_rejected(client, cycle, supply, kind, overrides, problem):
    response = create(client, kind, cycle["id"], supply["id"], **overrides)

    assert response.status_code == 422
    assert problem in " ".join(error["msg"] for error in response.json()["detail"])


def test_other_cultural_practice_keeps_its_detail(client, cycle, supply):
    record = create(
        client, "cultural-practices", cycle["id"], supply["id"],
        practice_type="other", other_detail="  Recolección de broca caída ",
    ).json()

    assert record["other_detail"] == "Recolección de broca caída"
    weeding = create(client, "cultural-practices", cycle["id"], supply["id"], other_detail="sobra").json()
    assert weeding["other_detail"] is None


# ── Insumos ──────────────────────────────────────────────────────────────


def test_inactive_supply_is_not_used_in_new_labors(client, login, admin, farmer, cycle, supply):
    record = create(client, "fertilizations", cycle["id"], supply["id"]).json()
    login(admin)
    client.post(f"{API}/supplies/{supply['id']}/deactivate")
    login(farmer)

    assert create(client, "fertilizations", cycle["id"], supply["id"]).status_code == 409
    body = {**payloads(supply["id"])["fertilizations"], "quantity": "130"}
    assert client.put(f"{API}/fertilizations/update/{record['id']}", json=body).status_code == 200, (
        "corregir un registro con su mismo insumo sigue siendo posible"
    )


def test_supply_in_use_is_not_deleted(client, login, admin, cycle, supply):
    create(client, "phytosanitary-apps", cycle["id"], supply["id"])
    login(admin)

    response = client.delete(f"{API}/supplies/delete/{supply['id']}")

    assert response.status_code == 409
    assert "Desactívalo" in response.json()["detail"]


def test_unknown_supply_is_not_found(client, cycle, supply):
    assert create(client, "fertilizations", cycle["id"], 999999).status_code == 404


# ── Registro en varios lotes ─────────────────────────────────────────────


@pytest.fixture
def farm_cycles(farm, create_plot, create_cycle):
    """Tres lotes de la finca, cada uno con su ciclo activo."""
    return [create_cycle(create_plot(farm["id"], name=f"Lote {n}")["id"]) for n in (1, 2, 3)]


def bulk(client, kind, body):
    return client.post(f"{API}/{kind}/bulk-create", json=body)


def test_bulk_creates_one_record_per_plot(client, farm_cycles, supply):
    quantities = ["50", "30", "20"]
    response = bulk(client, "fertilizations", {
        "supply_id": supply["id"], "application_date": "2025-03-01", "method": "soil",
        "items": [
            {"crop_cycle_id": cycle["id"], "quantity": quantity, "cost": None}
            for cycle, quantity in zip(farm_cycles, quantities)
        ],
    })

    assert response.status_code == 200, response.text
    records = response.json()
    assert [(r["plot_name"], r["quantity"]) for r in records] == [
        ("Lote 1", "50.000"), ("Lote 2", "30.000"), ("Lote 3", "20.000"),
    ]
    assert {r["application_date"] for r in records} == {"2025-03-01"}


def test_bulk_without_amounts(client, farm_cycles, supply):
    response = bulk(client, "flowering-records", {
        "flowering_date": "2025-03-01", "intensity": "medium",
        "items": [{"crop_cycle_id": cycle["id"]} for cycle in farm_cycles],
    })

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_bulk_is_all_or_nothing(client, farm_cycles, supply):
    client.post(f"{API}/crop-cycles/{farm_cycles[2]['id']}/close", json={"end_date": "2025-06-30"})

    response = bulk(client, "cultural-practices", {
        "practice_type": "weeding", "practice_date": "2025-03-01",
        "items": [{"crop_cycle_id": cycle["id"], "cost": "10000"} for cycle in farm_cycles],
    })

    assert response.status_code == 409
    assert "Lote 3" in response.json()["detail"]
    assert client.get(f"{API}/cultural-practices/get").json() == []


def test_bulk_date_is_checked_on_every_cycle(client, farm_cycles, create_cycle, create_plot, farm):
    late = create_cycle(create_plot(farm["id"], name="Lote tardío")["id"], start_date="2025-05-01")

    response = bulk(client, "irrigations", {
        "irrigation_date": "2025-03-01",
        "items": [{"crop_cycle_id": cycle["id"]} for cycle in [*farm_cycles, late]],
    })

    assert response.status_code == 409
    assert client.get(f"{API}/irrigations/get").json() == []


def test_bulk_stays_within_one_farm(client, farm_cycles, create_farm, create_plot, create_cycle):
    other_farm = create_farm(name="Otra finca")
    elsewhere = create_cycle(create_plot(other_farm["id"])["id"])

    response = bulk(client, "flowering-records", {
        "flowering_date": "2025-03-01", "intensity": "low",
        "items": [{"crop_cycle_id": farm_cycles[0]["id"]}, {"crop_cycle_id": elsewhere["id"]}],
    })

    assert response.status_code == 409


def test_bulk_lists_each_plot_once(client, farm_cycles):
    cycle_id = farm_cycles[0]["id"]

    response = bulk(client, "flowering-records", {
        "flowering_date": "2025-03-01", "intensity": "low",
        "items": [{"crop_cycle_id": cycle_id}, {"crop_cycle_id": cycle_id}],
    })

    assert response.status_code == 422


@pytest.mark.parametrize("kind", ["pest-monitorings", "soil-analyses"])
def test_measurements_of_each_plot_have_no_bulk(client, farm_cycles, kind):
    assert bulk(client, kind, {}).status_code in (404, 405)


# ── Alcance ──────────────────────────────────────────────────────────────


def test_labors_of_other_farmers_are_out_of_reach(client, login, make_farmer, cycle, supply):
    record = create(client, "irrigations", cycle["id"], supply["id"]).json()
    _, intruder = make_farmer("Otro")
    login(intruder)

    assert client.get(f"{API}/irrigations/get").json() == []
    body = payloads(supply["id"])["irrigations"]
    assert client.put(f"{API}/irrigations/update/{record['id']}", json=body).status_code == 404
    assert client.delete(f"{API}/irrigations/delete/{record['id']}").status_code == 404
    assert create(client, "irrigations", cycle["id"], supply["id"]).status_code == 404
    assert bulk(client, "irrigations", {
        "irrigation_date": "2025-03-01", "items": [{"crop_cycle_id": cycle["id"]}],
    }).status_code == 404
