"""
El módulo de Usuarios administra solo cuentas del personal (`admin`, `user`).

Las cuentas de caficultores se crean y administran desde el módulo de
cultivo: aquí no se listan, no se pueden consultar, editar ni eliminar, y
ninguna cuenta puede crearse o convertirse al rol `farmer` (plan de
implementación §2.2).
"""

import pytest

NEW_USER = {
    "username": "nuevo_test",
    "password": "secreto123",
    "person": {"full_name": "Nuevo Usuario", "phone": "3001234567"},
}


@pytest.fixture
def admin_client(make_user, login):
    return login(make_user("admin"))


def failed_fields(response):
    return {error["loc"][-1] for error in response.json()["detail"]}


def test_list_excludes_farmer_accounts(admin_client, make_user):
    make_user("user", "personal_test")
    make_user("farmer", "caficultor_test")

    response = admin_client.get("/api/v1/users/get")

    assert response.status_code == 200
    assert {u["username"] for u in response.json()} == {"admin_test", "personal_test"}


def test_filter_by_farmer_role_returns_nothing(admin_client, make_user):
    make_user("farmer", "caficultor_test")

    response = admin_client.get("/api/v1/users/get", params={"role": "farmer"})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/api/v1/users/get/user/{id}"),
        ("PUT", "/api/v1/users/update/{id}"),
        ("DELETE", "/api/v1/users/delete/{id}"),
    ],
)
def test_farmer_accounts_are_out_of_reach(admin_client, make_user, method, path):
    farmer = make_user("farmer", "caficultor_test")
    # Intento de convertir al caficultor en administrador
    body = {"role": "admin"} if method == "PUT" else None

    response = admin_client.request(method, path.format(id=farmer.id), json=body)

    assert response.status_code == 404


@pytest.mark.parametrize("role", ["farmer", "otro"])
def test_cannot_create_account_with_non_staff_role(admin_client, role):
    response = admin_client.post("/api/v1/users/create", json={**NEW_USER, "role": role})

    assert response.status_code == 422
    assert failed_fields(response) == {"role"}


def test_cannot_turn_staff_account_into_farmer(admin_client, make_user):
    staff = make_user("user", "personal_test")

    response = admin_client.put(f"/api/v1/users/update/{staff.id}", json={"role": "farmer"})

    assert response.status_code == 422
    assert failed_fields(response) == {"role"}


def test_staff_accounts_are_still_managed(admin_client):
    created = admin_client.post("/api/v1/users/create", json={**NEW_USER, "role": "user"})
    assert created.status_code == 200

    user_id = created.json()["id"]
    promoted = admin_client.put(f"/api/v1/users/update/{user_id}", json={"role": "admin"})

    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"
    assert admin_client.get(f"/api/v1/users/get/user/{user_id}").status_code == 200


def test_missing_user_returns_404(admin_client):
    assert admin_client.get("/api/v1/users/get/user/999999").status_code == 404
