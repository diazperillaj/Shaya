"""
Fincas: el administrador las registra a nombre de cualquier caficultor; un
caficultor solo ve y gestiona las suyas, y lo ajeno le responde 404.
"""

from tests.farm_operations.payloads import API, FARM


def test_admin_registers_farm_for_any_farmer(client, login, admin, make_farmer):
    farmer, _ = make_farmer("Ana")

    response = login(admin).post(f"{API}/farms/create", json={**FARM, "farmer_id": farmer.id})

    assert response.status_code == 200
    body = response.json()
    assert body["farmer"] == {"id": farmer.id, "full_name": "Ana 1"}
    assert body["active_plots"] == 0


def test_admin_must_choose_the_farmer(client, login, admin):
    response = login(admin).post(f"{API}/farms/create", json=FARM)

    assert response.status_code == 400


def test_farmer_registers_farm_under_own_name(client, login, make_farmer):
    farmer, user = make_farmer()

    response = login(user).post(f"{API}/farms/create", json=FARM)

    assert response.status_code == 200
    assert response.json()["farmer"]["id"] == farmer.id


def test_farmer_cannot_register_farm_for_someone_else(client, login, make_farmer):
    _, user = make_farmer()
    other, _ = make_farmer()

    response = login(user).post(f"{API}/farms/create", json={**FARM, "farmer_id": other.id})

    assert response.status_code == 403


def test_farmer_sees_only_own_farms(client, login, admin, make_farmer, create_farm):
    farmer_a, user_a = make_farmer()
    farmer_b, _ = make_farmer()
    login(admin)
    create_farm(name="Finca A", farmer_id=farmer_a.id)
    create_farm(name="Finca B", farmer_id=farmer_b.id)

    assert {f["name"] for f in client.get(f"{API}/farms/get").json()} == {"Finca A", "Finca B"}

    login(user_a)
    assert [f["name"] for f in client.get(f"{API}/farms/get").json()] == ["Finca A"]


def test_other_farmers_farm_is_not_found(client, login, make_farmer, create_farm):
    _, user_a = make_farmer()
    _, user_b = make_farmer()

    login(user_b)
    farm_b = create_farm(name="Finca B")

    login(user_a)
    assert client.get(f"{API}/farms/get/{farm_b['id']}").status_code == 404
    assert client.put(f"{API}/farms/update/{farm_b['id']}", json=FARM).status_code == 404
    assert client.delete(f"{API}/farms/delete/{farm_b['id']}").status_code == 404


def test_farm_name_is_unique_per_farmer(client, login, admin, make_farmer, create_farm):
    farmer_a, _ = make_farmer()
    farmer_b, _ = make_farmer()
    login(admin)
    create_farm(farmer_id=farmer_a.id)

    duplicate = client.post(f"{API}/farms/create", json={**FARM, "name": "la esperanza", "farmer_id": farmer_a.id})
    assert duplicate.status_code == 409

    # Otro caficultor puede tener una finca con el mismo nombre
    create_farm(farmer_id=farmer_b.id)


def test_farm_with_plots_cannot_be_deleted(client, login, make_farmer, create_farm, create_plot):
    _, user = make_farmer()
    login(user)
    farm = create_farm()
    empty = create_farm(name="Sin lotes")
    create_plot(farm["id"])

    assert client.delete(f"{API}/farms/delete/{farm['id']}").status_code == 409
    assert client.delete(f"{API}/farms/delete/{empty['id']}").status_code == 200


def test_farmer_account_without_farmer_record_sees_nothing(client, login, make_user):
    orphan = make_user("farmer", "sin_registro")
    login(orphan)

    assert client.get(f"{API}/farms/get").json() == []
    assert client.post(f"{API}/farms/create", json=FARM).status_code == 403
