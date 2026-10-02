"""
El asistente solo atiende al personal de Shaya: un caficultor (rol `farmer`)
recibe 403 aunque su sesión sea válida.

La consulta del usuario se reemplaza por una conexión falsa: la prueba no
necesita base de datos.
"""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from jose import jwt
from starlette.requests import Request

from app.core import security
from app.core.config import settings


class FakeConnection:
    def __init__(self, row):
        self.row = row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args, **kwargs):
        return SimpleNamespace(first=lambda: self.row)


def request_with_session():
    """Request con una cookie de sesión válida para el usuario 7."""
    token = jwt.encode({"sub": "7"}, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return Request({"type": "http", "headers": [(b"cookie", f"access_token={token}".encode())]})


@pytest.fixture
def user_with_role(monkeypatch):
    def _with_role(role):
        row = SimpleNamespace(id=7, username="usuario_test", role=role)
        engine = SimpleNamespace(connect=lambda: FakeConnection(row))
        monkeypatch.setattr(security, "business_engine", engine)
        return request_with_session()

    return _with_role


@pytest.mark.parametrize("role", ["admin", "user"])
def test_staff_can_use_the_assistant(user_with_role, role):
    user = security.get_current_user(user_with_role(role))

    assert user.role == role


@pytest.mark.parametrize("role", ["farmer", None, "otro"])
def test_non_staff_is_rejected(user_with_role, role):
    with pytest.raises(HTTPException) as denied:
        security.get_current_user(user_with_role(role))

    assert denied.value.status_code == 403


def test_missing_session_is_rejected():
    with pytest.raises(HTTPException) as denied:
        security.get_current_user(Request({"type": "http", "headers": []}))

    assert denied.value.status_code == 401
