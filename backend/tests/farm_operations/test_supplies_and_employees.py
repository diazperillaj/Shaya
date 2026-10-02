"""
Insumos (catálogo global, creación al vuelo) y empleados (por finca, dentro
del alcance del caficultor).
"""

import pytest

from tests.farm_operations.payloads import API

UREA = {"name": "Urea", "supply_type": "fertilizer", "unit": "kg", "composition": "46-0-0"}


@pytest.fixture
def farmer_client(client, login, make_farmer):
    _, user = make_farmer()
    return login(user)


# ── Insumos ──────────────────────────────────────────────────────────────


def test_farmer_adds_supplies_on_the_fly(farmer_client):
    response = farmer_client.post(f"{API}/supplies/create", json=UREA)

    assert response.status_code == 200
    assert response.json()["active"] is True


def test_supply_is_unique_per_name_and_type(farmer_client):
    farmer_client.post(f"{API}/supplies/create", json=UREA)

    assert farmer_client.post(f"{API}/supplies/create", json={**UREA, "name": "urea"}).status_code == 409
    other_type = {**UREA, "supply_type": "other", "other_detail": "Bioestimulante"}
    assert farmer_client.post(f"{API}/supplies/create", json=other_type).status_code == 200


def test_other_supply_type_needs_detail(farmer_client):
    response = farmer_client.post(f"{API}/supplies/create", json={**UREA, "supply_type": "other"})

    assert response.status_code == 422


def test_only_admin_deactivates_or_deletes_supplies(client, login, make_farmer, admin):
    _, user = make_farmer()
    supply = login(user).post(f"{API}/supplies/create", json=UREA).json()

    assert client.post(f"{API}/supplies/{supply['id']}/deactivate").status_code == 403
    assert client.delete(f"{API}/supplies/delete/{supply['id']}").status_code == 403

    login(admin)
    assert client.post(f"{API}/supplies/{supply['id']}/deactivate").json()["active"] is False
    assert client.get(f"{API}/supplies/get", params={"active": True}).json() == []
    assert client.delete(f"{API}/supplies/delete/{supply['id']}").status_code == 200


def test_supplies_filter_by_type_and_text(farmer_client):
    farmer_client.post(f"{API}/supplies/create", json=UREA)
    farmer_client.post(f"{API}/supplies/create", json={"name": "Glifosato", "supply_type": "herbicide", "unit": "L"})

    by_type = farmer_client.get(f"{API}/supplies/get", params={"supply_type": "herbicide"}).json()
    by_text = farmer_client.get(f"{API}/supplies/get", params={"search": "46-0"}).json()

    assert [s["name"] for s in by_type] == ["Glifosato"]
    assert [s["name"] for s in by_text] == ["Urea"]


# ── Empleados ────────────────────────────────────────────────────────────


def test_employees_belong_to_a_farm_of_the_farmer(client, login, make_farmer, create_farm):
    _, owner = make_farmer()
    login(owner)
    farm = create_farm()
    employee = client.post(f"{API}/employees/create", json={"farm_id": farm["id"], "full_name": " Pedro Pérez "}).json()
    assert employee["full_name"] == "Pedro Pérez"

    _, intruder = make_farmer()
    login(intruder)
    assert client.post(f"{API}/employees/create", json={"farm_id": farm["id"], "full_name": "X"}).status_code == 404
    assert client.get(f"{API}/employees/get").json() == []
    assert client.put(f"{API}/employees/update/{employee['id']}", json={"full_name": "X"}).status_code == 404


def test_deactivated_employee_leaves_the_active_list(client, login, make_farmer, create_farm):
    _, owner = make_farmer()
    login(owner)
    farm = create_farm()
    employee = client.post(f"{API}/employees/create", json={"farm_id": farm["id"], "full_name": "Pedro"}).json()

    client.post(f"{API}/employees/{employee['id']}/deactivate")

    assert client.get(f"{API}/employees/get", params={"farm_id": farm["id"], "active": True}).json() == []
    assert client.post(f"{API}/employees/{employee['id']}/activate").json()["active"] is True
