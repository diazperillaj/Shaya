"""
Jornales (trabajo pagado por día que no es recolección) y pagos: lo
pendiente por empleado, pago por selección en una transacción y pagos que
se pueden deshacer.
"""

import pytest

from tests.farm_operations.payloads import API


@pytest.fixture
def farm(client, login, make_farmer, create_farm):
    _, user = make_farmer()
    login(user)
    return create_farm()


@pytest.fixture
def plot(farm, create_plot):
    return create_plot(farm["id"])


@pytest.fixture
def employee(farm, create_employee):
    return create_employee(farm["id"], full_name="Ana Jornalera")


@pytest.fixture
def work(client, plot, employee, create_cycle, create_employee):
    """Recolección de 40 kg a $800 (pendiente de pago) de otro empleado."""
    cycle = create_cycle(plot["id"])
    picker = create_employee(plot["farm_id"], full_name="Beto Recolector")
    harvest = client.post(f"{API}/harvests/create", json={
        "crop_cycle_id": cycle["id"], "start_date": "2025-04-01", "rate_per_kg": "800",
    }).json()
    response = client.post(f"{API}/harvests/{harvest['id']}/works/create", json={
        "employee_id": picker["id"], "work_date": "2025-04-02", "kg_collected": "40",
    })
    assert response.status_code == 200, response.text
    return response.json()


def add_labor(client, employee_id, **overrides):
    body = {"employee_id": employee_id, "labor_date": "2025-04-03", "activity_type": "weeding", "daily_value": "55000"}
    return client.post(f"{API}/day-labors/create", json={**body, **overrides})


# ── Jornales ─────────────────────────────────────────────────────────────


def test_day_labor_is_recorded_with_its_plot(client, plot, employee):
    labor = add_labor(client, employee["id"], plot_id=plot["id"])

    assert labor.status_code == 200
    assert (labor.json()["plot_name"], labor.json()["paid"]) == (plot["name"], False)
    listed = client.get(f"{API}/day-labors/get", params={"farm_id": plot["farm_id"], "paid": False}).json()
    assert [item["id"] for item in listed] == [labor.json()["id"]]


def test_other_activity_needs_its_detail(client, employee):
    assert add_labor(client, employee["id"], activity_type="other").status_code == 422
    labor = add_labor(client, employee["id"], activity_type="other", other_detail=" Arreglo de caminos ")
    assert labor.json()["other_detail"] == "Arreglo de caminos"


def test_plot_must_be_of_the_employee_farm(client, employee, create_farm, create_plot):
    elsewhere = create_plot(create_farm(name="Otra finca")["id"])

    assert add_labor(client, employee["id"], plot_id=elsewhere["id"]).status_code == 409


def test_inactive_employee_takes_no_new_labors(client, employee):
    client.post(f"{API}/employees/{employee['id']}/deactivate")

    assert add_labor(client, employee["id"]).status_code == 409


# ── Pagos ────────────────────────────────────────────────────────────────


def test_pending_lists_work_and_labors_by_employee(client, farm, employee, work):
    labor = add_labor(client, employee["id"]).json()

    items = client.get(f"{API}/payments/get", params={"farm_id": farm["id"], "paid": False}).json()

    assert [(i["employee_name"], i["kind"], i["amount"]) for i in items] == [
        ("Ana Jornalera", "day_labor", "55000.00"),
        ("Beto Recolector", "harvest_work", "32000.00"),
    ]
    assert items[1]["pass_number"] == 1 and items[1]["kg_collected"] == "40.000"
    assert items[0]["id"] == labor["id"]


def test_selection_is_paid_in_one_operation(client, farm, employee, work):
    labor = add_labor(client, employee["id"]).json()

    result = client.post(f"{API}/payments/pay", json={
        "harvest_work_ids": [work["id"]], "day_labor_ids": [labor["id"]], "paid_at": "2025-04-05",
    })

    assert result.json() == {"count": 2, "total": "87000.00"}
    assert client.get(f"{API}/payments/get", params={"farm_id": farm["id"], "paid": False}).json() == []
    paid = client.get(f"{API}/payments/get", params={"paid": True}).json()
    assert {item["paid_at"] for item in paid} == {"2025-04-05"}


def test_paying_twice_changes_nothing(client, work):
    selection = {"harvest_work_ids": [work["id"]], "paid_at": "2025-04-05"}
    client.post(f"{API}/payments/pay", json=selection)

    assert client.post(f"{API}/payments/pay", json=selection).json() == {"count": 0, "total": "0"}


def test_paid_items_are_frozen_until_unpaid(client, employee, work):
    labor = add_labor(client, employee["id"]).json()
    client.post(f"{API}/payments/pay", json={"harvest_work_ids": [work["id"]], "day_labor_ids": [labor["id"]]})

    work_body = {"employee_id": work["employee_id"], "work_date": "2025-04-02", "kg_collected": "45"}
    assert client.put(f"{API}/harvests/works/update/{work['id']}", json=work_body).status_code == 409
    assert client.delete(f"{API}/harvests/works/delete/{work['id']}").status_code == 409
    labor_body = {"employee_id": employee["id"], "activity_type": "weeding", "daily_value": "60000"}
    assert client.put(f"{API}/day-labors/update/{labor['id']}", json=labor_body).status_code == 409
    assert client.delete(f"{API}/day-labors/delete/{labor['id']}").status_code == 409

    undone = client.post(f"{API}/payments/unpay", json={"harvest_work_ids": [work["id"]], "day_labor_ids": [labor["id"]]})
    assert undone.json()["count"] == 2
    assert client.put(f"{API}/harvests/works/update/{work['id']}", json=work_body).json()["total_value"] == "36000.00"


@pytest.mark.parametrize(
    "body, status",
    [
        ({}, 422),
        ({"paid_at": "2999-01-01"}, 422),
        ({"paid_at": "2025-04-01"}, 409),
    ],
)
def test_invalid_payments_are_rejected(client, work, body, status):
    selection = {"harvest_work_ids": [work["id"]]} if body else {}

    assert client.post(f"{API}/payments/pay", json={**selection, **body}).status_code == status


def test_payments_stay_within_reach(client, login, make_farmer, work):
    _, intruder = make_farmer("Otro")
    login(intruder)

    assert client.get(f"{API}/payments/get").json() == []
    assert client.post(f"{API}/payments/pay", json={"harvest_work_ids": [work["id"]]}).status_code == 404


# ── Historial que bloquea borrados ───────────────────────────────────────


def test_employee_with_history_is_deactivated_not_deleted(client, work):
    response = client.delete(f"{API}/employees/delete/{work['employee_id']}")

    assert response.status_code == 409
    assert "Desactívalo" in response.json()["detail"]


def test_plot_with_day_labors_is_not_deleted(client, plot, employee):
    add_labor(client, employee["id"], plot_id=plot["id"])

    assert client.delete(f"{API}/plots/delete/{plot['id']}").status_code == 409
