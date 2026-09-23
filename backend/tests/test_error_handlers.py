"""
Contrato de errores (especificacion-api §1): 422 con detalle para cualquier
error de validación, 400 con mensaje propio para los campos que lo tienen, y
los errores de dominio con su código.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.exceptions.domain import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from app.core.exceptions.handlers import register_exception_handlers


class Payload(BaseModel):
    cherry_kg: float
    phone: str | None = None


@pytest.fixture(scope="module")
def error_client():
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/validate")
    def validate(payload: Payload):
        return payload

    @app.get("/raise/{kind}")
    def raise_domain_error(kind: str):
        errors = {
            "not-found": NotFoundError,
            "conflict": ConflictError,
            "forbidden": PermissionDeniedError,
        }
        raise errors[kind]("detalle del error")

    return TestClient(app)


def test_unmapped_validation_error_returns_422_with_detail(error_client):
    response = error_client.post("/validate", json={"cherry_kg": "abc"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "cherry_kg"]


def test_mapped_validation_error_keeps_custom_message(error_client):
    response = error_client.post("/validate", json={"cherry_kg": 1, "phone": 123})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "El número debe ser un valor númerico de 10 caracteres"
    }


@pytest.mark.parametrize(
    "kind, status",
    [("not-found", 404), ("conflict", 409), ("forbidden", 403)],
)
def test_domain_errors_map_to_their_status(error_client, kind, status):
    response = error_client.get(f"/raise/{kind}")

    assert response.status_code == status
    assert response.json() == {"detail": "detalle del error"}
