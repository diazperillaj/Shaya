"""
Auditoría del control de acceso por rol sobre todas las rutas de la API.

Las rutas se descubren de la propia app: un router nuevo queda cubierto sin
tocar este archivo, y si nace sin el guardia correcto estas pruebas fallan
(plan de implementación §2.1).
"""

import re
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.api.api_v1.auth.dependencies import require_staff
from app.farm_operations.api.v1.dependencies import require_farm_role
from app.main import app

API_PREFIX = "/api/v1/"
AUTH_PREFIX = "/api/v1/auth/"
# Con la barra final: /api/v1/farmers no es parte del módulo de cultivo
FARM_PREFIX = "/api/v1/farm/"

# Únicas rutas de la API que no exigen sesión
PUBLIC_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
}

ROUTES = sorted(
    (method, route.path)
    for route in app.routes
    if isinstance(route, APIRoute) and route.path.startswith(API_PREFIX)
    for method in route.methods
)
PRIVATE_ROUTES = [r for r in ROUTES if r not in PUBLIC_ROUTES]
BUSINESS_ROUTES = [r for r in ROUTES if not r[1].startswith((AUTH_PREFIX, FARM_PREFIX))]
FARM_ROUTES = [r for r in ROUTES if r[1].startswith(FARM_PREFIX)]


def route_id(route):
    return " ".join(route)


def call(client, method, path):
    """Llama la ruta con parámetros de ruta ficticios y cuerpo vacío.

    Los guardias de acceso son dependencias, y FastAPI las resuelve antes de
    validar parámetros y cuerpo: la respuesta refleja solo el control de acceso.
    """
    url = re.sub(r"\{[^}]+\}", "1", path)
    body = {} if method in {"POST", "PUT", "PATCH"} else None
    return client.request(method, url, json=body)


@pytest.fixture
def farmer_client(make_user, login):
    return login(make_user("farmer"))


@pytest.fixture
def staff_client(make_user, login):
    return login(make_user("user"))


def test_audit_sees_every_module():
    # Si el descubrimiento fallara, las pruebas parametrizadas pasarían sin
    # revisar nada.
    modules = {path.split("/")[3] for _, path in ROUTES}

    assert {"auth", "users", "farmers", "inventory", "sales", "dashboard"} <= modules


@pytest.mark.parametrize("method, path", PRIVATE_ROUTES, ids=map(route_id, PRIVATE_ROUTES))
def test_private_routes_require_a_session(client, method, path):
    assert call(client, method, path).status_code == 401


@pytest.mark.parametrize("method, path", BUSINESS_ROUTES, ids=map(route_id, BUSINESS_ROUTES))
def test_farmer_cannot_reach_business_modules(farmer_client, method, path):
    assert call(farmer_client, method, path).status_code == 403


@pytest.mark.parametrize("method, path", FARM_ROUTES, ids=map(route_id, FARM_ROUTES))
def test_staff_user_cannot_reach_farm_module(staff_client, method, path):
    assert call(staff_client, method, path).status_code == 403


def test_farmer_keeps_its_session_routes(farmer_client):
    me = farmer_client.get("/api/v1/auth/me")

    assert me.status_code == 200
    assert me.json()["role"] == "farmer"
    assert farmer_client.post("/api/v1/auth/logout").status_code == 200


def test_staff_keeps_access_to_business_modules(staff_client):
    assert staff_client.get("/api/v1/customers/get").status_code == 200


@pytest.mark.parametrize(
    "role, allowed",
    [("admin", True), ("user", True), ("farmer", False), (None, False), ("otro", False)],
)
def test_require_staff(role, allowed):
    check_guard(require_staff, role, allowed)


@pytest.mark.parametrize(
    "role, allowed",
    [("admin", True), ("farmer", True), ("user", False), (None, False), ("otro", False)],
)
def test_require_farm_role(role, allowed):
    check_guard(require_farm_role, role, allowed)


def check_guard(guard, role, allowed):
    user = SimpleNamespace(role=role)

    if allowed:
        assert guard(user) is user
    else:
        with pytest.raises(HTTPException) as denied:
            guard(user)
        assert denied.value.status_code == 403
