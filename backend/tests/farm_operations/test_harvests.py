"""
Cosechas: pasadas numeradas, una abierta por ciclo, recolección al peso o
por jornal con su valor calculado, y cierre con el total de café cereza.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.farm_operations.models import HarvestWork
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
def cycle(farm, create_plot, create_cycle):
    return create_cycle(create_plot(farm["id"])["id"])


@pytest.fixture
def employee(farm, create_employee):
    return create_employee(farm["id"])


@pytest.fixture
def open_harvest(client, cycle):
    def _open(**overrides) -> dict:
        body = {"crop_cycle_id": cycle["id"], "start_date": "2025-04-01", "rate_per_kg": "800", "rate_per_day": "60000"}
        response = client.post(f"{API}/harvests/create", json={**body, **overrides})
        assert response.status_code == 200, response.text
        return response.json()

    return _open


def add_work(client, harvest_id, employee_id, **overrides):
    body = {"employee_id": employee_id, "work_date": "2025-04-02", "kg_collected": "40"}
    return client.post(f"{API}/harvests/{harvest_id}/works/create", json={**body, **overrides})


def close(client, harvest_id, **body):
    return client.post(f"{API}/harvests/{harvest_id}/close", json={"end_date": "2025-04-10", **body})


# ── Apertura ─────────────────────────────────────────────────────────────


def test_passes_are_numbered_and_one_is_open_at_a_time(client, cycle, employee, open_harvest):
    first = open_harvest()
    assert first["pass_number"] == 1

    second_while_open = client.post(f"{API}/harvests/create", json={"crop_cycle_id": cycle["id"], "start_date": "2025-04-05"})
    assert second_while_open.status_code == 409
    assert "pasada 1" in second_while_open.json()["detail"]

    add_work(client, first["id"], employee["id"])
    close(client, first["id"])
    assert open_harvest(start_date="2025-05-01")["pass_number"] == 2


def test_harvest_belongs_to_an_active_cycle(client, cycle):
    before_cycle = client.post(f"{API}/harvests/create", json={"crop_cycle_id": cycle["id"], "start_date": "2025-01-01"})
    assert before_cycle.status_code == 409

    client.post(f"{API}/crop-cycles/{cycle['id']}/close", json={"end_date": "2025-12-01"})
    closed = client.post(f"{API}/harvests/create", json={"crop_cycle_id": cycle["id"], "start_date": "2025-04-01"})
    assert closed.status_code == 409


# ── Recolección ──────────────────────────────────────────────────────────


def test_per_kg_work_is_valued_at_the_session_rate(client, employee, open_harvest):
    harvest = open_harvest()

    work = add_work(client, harvest["id"], employee["id"], kg_collected="12.345").json()

    assert (work["rate_per_kg"], work["total_value"]) == ("800.00", "9876.00")
    assert work["employee_name"] == employee["full_name"]

    own_rate = add_work(client, harvest["id"], employee["id"], kg_collected="10", rate_per_kg="1000.50").json()
    assert own_rate["total_value"] == "10005.00"


def test_per_day_work_is_valued_at_the_day_rate(client, employee, open_harvest):
    harvest = open_harvest()

    work = add_work(client, harvest["id"], employee["id"], payment_type="per_day", kg_collected=None).json()

    assert (work["day_value"], work["total_value"], work["rate_per_kg"]) == ("60000.00", "60000.00", None)


@pytest.mark.parametrize(
    "payment_type, problem",
    [("per_kg", "tarifa por kg"), ("per_day", "valor del jornal")],
)
def test_a_rate_is_needed_when_the_session_has_none(client, employee, open_harvest, payment_type, problem):
    harvest = open_harvest(rate_per_kg=None, rate_per_day=None)

    response = add_work(client, harvest["id"], employee["id"], payment_type=payment_type)

    assert response.status_code == 400
    assert problem in response.json()["detail"]


def test_per_kg_work_needs_its_kg(client, employee, open_harvest):
    harvest = open_harvest()

    assert add_work(client, harvest["id"], employee["id"], kg_collected=None).status_code == 422


def test_database_checks_the_payment_mode(db_session, employee, open_harvest):
    harvest = open_harvest()
    db_session.add(HarvestWork(
        harvest_id=harvest["id"], employee_id=employee["id"], work_date=date(2025, 4, 2),
        payment_type="per_kg", kg_collected=Decimal(5), total_value=Decimal(0),
    ))

    with pytest.raises(IntegrityError, match="ck_harvest_works_payment"):
        db_session.flush()


def test_only_active_employees_of_the_farm_collect(client, farm, create_farm, create_employee, employee, open_harvest):
    harvest = open_harvest()
    stranger = create_employee(create_farm(name="Otra finca")["id"], full_name="Ajeno")
    assert add_work(client, harvest["id"], stranger["id"]).status_code == 409

    client.post(f"{API}/employees/{employee['id']}/deactivate")
    assert add_work(client, harvest["id"], employee["id"]).status_code == 409


def test_work_date_is_not_before_the_harvest(client, employee, open_harvest):
    harvest = open_harvest()

    assert add_work(client, harvest["id"], employee["id"], work_date="2025-03-30").status_code == 409


# ── Cierre, totales y reapertura ─────────────────────────────────────────


def test_close_preloads_the_registered_kg(client, employee, open_harvest):
    harvest = open_harvest()
    add_work(client, harvest["id"], employee["id"], kg_collected="40")
    add_work(client, harvest["id"], employee["id"], payment_type="per_day", kg_collected="25.5")
    add_work(client, harvest["id"], employee["id"], payment_type="per_day", kg_collected=None)

    closed = close(client, harvest["id"])

    assert closed.status_code == 200
    body = closed.json()
    assert (body["status"], body["total_cherry_kg"], body["kg_registered"]) == ("closed", "65.500", "65.500")
    assert (body["works_count"], body["value_total"], body["value_pending"]) == (3, "152000.00", "152000.00")


def test_close_accepts_the_weighed_total(client, employee, open_harvest):
    harvest = open_harvest()
    add_work(client, harvest["id"], employee["id"], kg_collected="40")

    closed = close(client, harvest["id"], total_cherry_kg="55")

    assert closed.json()["total_cherry_kg"] == "55.000", "incluye la recolección familiar no paga"


def test_close_without_kg_needs_a_total(client, open_harvest):
    harvest = open_harvest()

    assert close(client, harvest["id"]).status_code == 400
    assert close(client, harvest["id"], total_cherry_kg="0").status_code == 200


def test_closed_harvest_freezes_its_works(client, employee, open_harvest):
    harvest = open_harvest()
    work = add_work(client, harvest["id"], employee["id"]).json()
    close(client, harvest["id"])

    assert add_work(client, harvest["id"], employee["id"]).status_code == 409
    body = {"employee_id": employee["id"], "work_date": "2025-04-02", "kg_collected": "50"}
    assert client.put(f"{API}/harvests/works/update/{work['id']}", json=body).status_code == 409
    assert client.delete(f"{API}/harvests/works/delete/{work['id']}").status_code == 409
    assert close(client, harvest["id"]).status_code == 409, "ya está cerrada"


def test_close_covers_the_works(client, employee, open_harvest):
    harvest = open_harvest()
    add_work(client, harvest["id"], employee["id"], work_date="2025-04-08")

    assert close(client, harvest["id"], end_date="2025-04-05").status_code == 409


def test_only_the_last_pass_reopens(client, employee, open_harvest):
    first = open_harvest()
    close(client, first["id"], total_cherry_kg="10")
    second = open_harvest(start_date="2025-05-01")
    close(client, second["id"], end_date="2025-05-10", total_cherry_kg="12")

    assert client.post(f"{API}/harvests/{first['id']}/reopen").status_code == 409

    reopened = client.post(f"{API}/harvests/{second['id']}/reopen").json()
    assert (reopened["status"], reopened["end_date"], reopened["total_cherry_kg"]) == ("open", None, None)


def test_closed_harvest_corrections_keep_its_total(client, open_harvest):
    harvest = open_harvest()
    url = f"{API}/harvests/update/{harvest['id']}"
    assert client.put(url, json={"start_date": "2025-04-01", "end_date": "2025-04-10"}).status_code == 409, (
        "una cosecha abierta no tiene fin"
    )

    close(client, harvest["id"], total_cherry_kg="30")
    assert client.put(url, json={"start_date": "2025-04-01"}).status_code == 409, "necesita fin y total"
    updated = client.put(url, json={"start_date": "2025-04-01", "end_date": "2025-04-11", "total_cherry_kg": "32"})
    assert updated.json()["total_cherry_kg"] == "32.000"


def test_only_harvests_without_works_are_deleted(client, employee, open_harvest):
    harvest = open_harvest()
    work = add_work(client, harvest["id"], employee["id"]).json()

    assert client.delete(f"{API}/harvests/delete/{harvest['id']}").status_code == 409
    client.delete(f"{API}/harvests/works/delete/{work['id']}")
    assert client.delete(f"{API}/harvests/delete/{harvest['id']}").status_code == 200


# ── Relación con el ciclo y alcance ──────────────────────────────────────


def test_cycle_closes_after_its_harvests(client, cycle, employee, open_harvest):
    harvest = open_harvest()
    add_work(client, harvest["id"], employee["id"])
    url = f"{API}/crop-cycles/{cycle['id']}/close"

    assert client.post(url, json={"end_date": "2025-12-01"}).status_code == 409
    close(client, harvest["id"])
    assert client.post(url, json={"end_date": "2025-04-05"}).status_code == 409, "antes del fin de la cosecha"
    assert client.post(url, json={"end_date": "2025-12-01"}).status_code == 200


def test_cycle_with_harvests_is_not_deleted(client, cycle, open_harvest):
    open_harvest()

    assert client.delete(f"{API}/crop-cycles/delete/{cycle['id']}").status_code == 409


def test_harvests_of_other_farmers_are_out_of_reach(client, login, make_farmer, cycle, employee, open_harvest):
    harvest = open_harvest()
    work = add_work(client, harvest["id"], employee["id"]).json()
    _, intruder = make_farmer("Otro")
    login(intruder)

    assert client.get(f"{API}/harvests/get").json() == []
    assert client.get(f"{API}/harvests/get/{harvest['id']}").status_code == 404
    assert add_work(client, harvest["id"], employee["id"]).status_code == 404
    assert client.delete(f"{API}/harvests/works/delete/{work['id']}").status_code == 404
    assert client.post(f"{API}/harvests/create", json={"crop_cycle_id": cycle["id"]}).status_code == 404
