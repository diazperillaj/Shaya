from dataclasses import dataclass

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy import text

from app.core.config import settings
from app.core.db import business_engine


@dataclass(frozen=True)
class CurrentUser:
    id: int
    username: str
    role: str | None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def get_current_user(request: Request) -> CurrentUser:
    """
    Valida la MISMA cookie de sesión del backend (access_token, JWT HS256
    firmado con el SECRET_KEY compartido) y verifica que el usuario exista.
    No hay llamadas entre servicios: la verificación es local + una consulta
    de solo lectura a public.users.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    with business_engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, username, role FROM users WHERE id = :id"),
            {"id": int(payload["sub"])},
        ).first()

    if not row:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return CurrentUser(id=row.id, username=row.username, role=row.role)
