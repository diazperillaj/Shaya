"""
Ciclos productivos: uno activo por lote, numerados, sin solaparse y con un
rango de fechas que siempre cubre sus labores.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.farm_operations.models import CropCycle
from tests.farm_operations.payloads import API


@pytest.fixture
def farm(client, login, make_farmer, create_farm):
    """Finca de un caficultor con la sesión de ese caficultor abierta."""
    _, user = make_farmer()
    login(user)
    return create_farm()


@pytest.fixture
def plot(farm, create_plot):
    return create_plot(farm["id"])


def close(client, cycle_id, end_date="2025-12-20"):
    return client.post(f"{API}/crop-cycles/{cycle_id}/close", json={"end_date": end_date})


def add_flowering(client, cycle_id, flowering_date):
    return client.post(f"{API}/flowering-records/create", json={
        "crop_cycle_id": cycle_id, "flowering_date": flowering_date, "intensity": "high",
    })


# ── Apertura ─────────────────────────────────────────────────────────────


def test_cycles_are_numbered_per_plot(client, plot, create_cycle):
    first = create_cycle(plot["id"])
    close(client, first["id"])
    second = create_cycle(plot["id"], start_date="2026-01-10")

    assert (first["cycle_number"], second["cycle_number"]) == (1, 2)
    assert second["status"] == "active"
    assert client.get(f"{API}/plots/get/{plot['id']}").json()["active_cycle"] == {
        "id": second["id"], "cycle_number": 2, "start_date": "2026-01-10",
    }


def test_only_one_active_cycle_per_plot(client, plot, create_cycle):
    first = create_cycle(plot["id"])

    response = client.post(f"{API}/crop-cycles/create", json={"plot_id": plot["id"], "start_date": "2025-02-01"})

    assert response.status_code == 409
    assert f"ciclo {first['cycle_number']}" in response.json()["detail"]


def test_database_allows_a_single_active_cycle(db_session, plot, create_cycle):
    create_cycle(plot["id"])
    db_session.add(CropCycle(plot_id=plot["id"], cycle_number=2, start_date=date(2025, 6, 1)))

    with pytest.raises(IntegrityError, match="uq_crop_cycles_one_active"):
        db_session.flush()


@pytest.mark.parametrize(
    "start_date, problem",
    [
        ("2019-01-01", "antes de la siembra"),
        ("2025-12-01", "antes de que termine el ciclo 1"),
    ],
)
def test_cycles_do_not_overlap(client, plot, create_cycle, start_date, problem):
    first = create_cycle(plot["id"])
    close(client, first["id"])

    response = client.post(f"{API}/crop-cycles/create", json={"plot_id": plot["id"], "start_date": start_date})

    assert response.status_code == 409
    assert problem in response.json()["detail"]


def test_closed_plot_takes_no_cycles(client, plot):
    client.post(f"{API}/plots/{plot['id']}/close", json={})

    response = client.post(f"{API}/crop-cycles/create", json={"plot_id": plot["id"]})

    assert response.status_code == 409


def test_future_start_is_rejected(client, plot):
    response = client.post(f"{API}/crop-cycles/create", json={"plot_id": plot["id"], "start_date": "2999-01-01"})

    assert response.status_code == 422


# ── Cierre, reapertura y fechas ──────────────────────────────────────────


def test_close_cannot_leave_labors_outside_the_cycle(client, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    add_flowering(client, cycle["id"], "2025-04-10")

    assert close(client, cycle["id"], "2025-04-01").status_code == 409
    assert close(client, cycle["id"], "2025-01-10").status_code == 409, "antes del inicio"

    closed = close(client, cycle["id"], "2025-04-10")
    assert closed.status_code == 200
    assert (closed.json()["status"], closed.json()["end_date"]) == ("closed", "2025-04-10")
    assert close(client, cycle["id"]).status_code == 409, "ya está cerrado"


def test_update_keeps_labors_inside_the_cycle(client, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    add_flowering(client, cycle["id"], "2025-04-10")
    url = f"{API}/crop-cycles/update/{cycle['id']}"

    assert client.put(url, json={"start_date": "2025-05-01"}).status_code == 409
    assert client.put(url, json={"start_date": "2025-01-15", "end_date": "2025-06-01"}).status_code == 409, (
        "un ciclo activo no tiene fecha de fin"
    )

    updated = client.put(url, json={"start_date": "2025-02-01", "observations": "Inicio de lluvias"})
    assert updated.status_code == 200
    assert updated.json()["start_date"] == "2025-02-01"


def test_closed_cycle_end_can_be_corrected(client, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    close(client, cycle["id"])
    url = f"{API}/crop-cycles/update/{cycle['id']}"

    assert client.put(url, json={"start_date": "2025-01-15"}).status_code == 409, "necesita fecha de fin"
    assert client.put(url, json={"start_date": "2025-01-15", "end_date": "2025-11-30"}).json()["end_date"] == "2025-11-30"


def test_only_the_last_cycle_reopens(client, plot, create_cycle):
    first = create_cycle(plot["id"])
    close(client, first["id"])
    second = create_cycle(plot["id"], start_date="2026-01-10")
    close(client, second["id"], "2026-03-01")

    assert client.post(f"{API}/crop-cycles/{first['id']}/reopen").status_code == 409

    reopened = client.post(f"{API}/crop-cycles/{second['id']}/reopen")
    assert reopened.status_code == 200
    assert (reopened.json()["status"], reopened.json()["end_date"]) == ("active", None)


def test_cycles_of_a_closed_plot_do_not_reopen(client, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    close(client, cycle["id"])
    client.post(f"{API}/plots/{plot['id']}/close", json={})

    assert client.post(f"{API}/crop-cycles/{cycle['id']}/reopen").status_code == 409


# ── Relación con el lote ─────────────────────────────────────────────────


def test_plot_closes_only_without_active_cycle(client, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    url = f"{API}/plots/{plot['id']}/close"

    assert client.post(url, json={}).status_code == 409
    close(client, cycle["id"])
    assert client.post(url, json={"closed_at": "2025-12-01"}).status_code == 409, "antes del fin del último ciclo"
    assert client.post(url, json={"closed_at": "2025-12-20"}).status_code == 200


def test_plot_with_cycles_is_not_deleted(client, plot, create_cycle):
    create_cycle(plot["id"])

    assert client.delete(f"{API}/plots/delete/{plot['id']}").status_code == 409


# ── Borrado, detalle y alcance ───────────────────────────────────────────


def test_only_cycles_without_labors_are_deleted(client, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    add_flowering(client, cycle["id"], "2025-04-10")

    assert client.delete(f"{API}/crop-cycles/delete/{cycle['id']}").status_code == 409

    labor = client.get(f"{API}/flowering-records/get", params={"crop_cycle_id": cycle["id"]}).json()[0]
    client.delete(f"{API}/flowering-records/delete/{labor['id']}")
    assert client.delete(f"{API}/crop-cycles/delete/{cycle['id']}").status_code == 200


def test_detail_summarizes_labors_by_type(client, plot, create_cycle, create_supply):
    cycle = create_cycle(plot["id"])
    supply = create_supply()
    for day, cost in (("2025-03-01", "50000"), ("2025-06-01", "70000")):
        client.post(f"{API}/fertilizations/create", json={
            "crop_cycle_id": cycle["id"], "supply_id": supply["id"], "application_date": day,
            "method": "soil", "quantity": "100", "cost": cost,
        })
    add_flowering(client, cycle["id"], "2025-04-10")

    summary = {item["kind"]: item for item in client.get(f"{API}/crop-cycles/get/{cycle['id']}").json()["summary"]}

    assert summary["fertilizations"] == {
        "kind": "fertilizations", "count": 2, "last_date": "2025-06-01", "total_cost": "120000.00",
    }
    assert summary["flowering-records"]["count"] == 1
    assert summary["flowering-records"]["total_cost"] is None
    assert summary["irrigations"]["count"] == 0


def test_cycles_of_other_farmers_are_not_found(client, login, make_farmer, plot, create_cycle):
    cycle = create_cycle(plot["id"])
    _, intruder = make_farmer("Otro")
    login(intruder)

    assert client.get(f"{API}/crop-cycles/get/{cycle['id']}").status_code == 404
    assert close(client, cycle["id"]).status_code == 404
    assert client.get(f"{API}/crop-cycles/get").json() == []
    assert client.post(f"{API}/crop-cycles/create", json={"plot_id": plot["id"]}).status_code == 404
