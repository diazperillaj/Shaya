from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.roles import STAFF_ROLES
from app.core.security import decode_token
from app.core.db.session import get_db
from app.models.user import User

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).get(payload["sub"])

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="No tienes permisos")
    return current_user


def require_staff(current_user=Depends(get_current_user)):
    """
    Restringe el acceso al personal de Shaya (roles `admin` y `user`).

    Protege los módulos del negocio: un caficultor recibe 403 aunque tenga
    sesión iniciada.
    """
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    return current_user