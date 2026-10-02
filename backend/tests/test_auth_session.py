"""
Las fixtures de sesión reproducen el login real: la cookie con el token abre
las rutas protegidas y sin ella se rechazan.
"""


def test_protected_route_requires_session(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_session_cookie_opens_protected_route(make_user, login):
    user = make_user("admin")

    response = login(user).get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == user.username
