"""
Cuentas de caficultor: solo las crea un administrador (no hay autoregistro),
y una cuenta es la misma persona del registro de caficultor.
"""

import pytest

from app.models.farmer import Farmer
from app.models.person import Person
from app.models.user import User
from tests.farm_operations.payloads import API, FARM, PLOT

NEW_FARMER = {
    "farm_name": "Registro de compra",
    "village": "El Diviso",
    "municipality": "Pitalito",
    "person": {"full_name": "maria de los angeles ruiz", "phone": "3001234567"},
    "username": "maria_ruiz",
    "password": "secreto123",
}


@pytest.fixture
def admin_client(client, login, admin):
    return login(admin)


@pytest.mark.parametrize(
    "method, path",
    [("GET", "/farmer-accounts/get"), ("POST", "/farmer-accounts/create"), ("POST", "/farmer-accounts/create-full")],
)
def test_only_admins_manage_accounts(client, login, make_farmer, method, path):
    _, user = make_farmer()

    response = login(user).request(method, f"{API}{path}", json={} if method == "POST" else None)

    assert response.status_code == 403


def test_admin_gives_access_to_an_existing_farmer(admin_client, db_session):
    person = Person(full_name="Tito Novoa")
    farmer = Farmer(farm_name="Buenavista", village="Richa", municipality="Somondoco", person=person)
    db_session.add(farmer)
    db_session.flush()

    response = admin_client.post(
        f"{API}/farmer-accounts/create",
        json={"farmer_id": farmer.id, "username": "tito_novoa", "password": "secreto123"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "tito_novoa"
    user = db_session.query(User).filter(User.username == "tito_novoa").one()
    assert (user.role, user.person_id) == ("farmer", person.id)


def test_a_farmer_gets_one_account_and_usernames_are_unique(admin_client, make_farmer):
    farmer, user = make_farmer()

    again = admin_client.post(
        f"{API}/farmer-accounts/create",
        json={"farmer_id": farmer.id, "username": "otro_nombre", "password": "secreto123"},
    )
    taken = admin_client.post(f"{API}/farmer-accounts/create-full", json={**NEW_FARMER, "username": user.username})

    assert again.status_code == 409
    assert taken.status_code == 409


def test_failed_full_registration_leaves_nothing_behind(admin_client, db_session, make_farmer):
    _, user = make_farmer()

    admin_client.post(f"{API}/farmer-accounts/create-full", json={**NEW_FARMER, "username": user.username})

    assert db_session.query(Person).filter(Person.full_name.ilike("maria%")).count() == 0


def test_new_farmer_with_account_can_work_on_their_farm(client, admin_client):
    """El flujo con el que termina el bloque 1B (plan de implementación)."""
    created = admin_client.post(f"{API}/farmer-accounts/create-full", json=NEW_FARMER)
    assert created.status_code == 200
    assert created.json()["full_name"] == "Maria de los Angeles Ruiz"
    assert created.json()["account_role"] == "farmer"

    client.cookies.clear()
    login = client.post("/api/v1/auth/login", json={"username": "maria_ruiz", "password": "secreto123"})
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").json()["role"] == "farmer"
    assert client.get("/api/v1/sales/get").status_code == 403

    farm = client.post(f"{API}/farms/create", json=FARM).json()
    assert farm["farmer"]["full_name"] == "Maria de los Angeles Ruiz"
    plot = client.post(f"{API}/plots/create", json={**PLOT, "farm_id": farm["id"]})
    employee = client.post(f"{API}/employees/create", json={"farm_id": farm["id"], "full_name": "Pedro"})
    supply = client.post(f"{API}/supplies/create", json={"name": "DAP", "supply_type": "fertilizer"})

    assert (plot.status_code, employee.status_code, supply.status_code) == (200, 200, 200)
    assert client.get(f"{API}/farms/get/{farm['id']}").json()["active_plots"] == 1


def test_accounts_list_shows_who_has_access(admin_client, make_farmer, db_session):
    farmer, user = make_farmer()
    without = Farmer(farm_name="Sin cuenta", village="Vereda", municipality="Municipio",
                     person=Person(full_name="Sin Cuenta"))
    db_session.add(without)
    db_session.flush()

    accounts = {a["farmer_id"]: a for a in admin_client.get(f"{API}/farmer-accounts/get").json()}

    assert accounts[farmer.id]["username"] == user.username
    assert accounts[without.id]["username"] is None
