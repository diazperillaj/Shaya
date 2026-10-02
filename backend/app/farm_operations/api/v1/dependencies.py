from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user
from app.core.db.session import get_db
from app.core.roles import FARM_ROLES
from app.farm_operations.services.access import FarmAccess


def require_farm_role(current_user=Depends(get_current_user)):
    """
    Acceso al módulo de cultivo: administradores y caficultores.

    El rol `user` (personal de Shaya) no opera el cultivo y recibe 403. El
    alcance por finca (cada caficultor solo ve las suyas) lo aplica
    `FarmAccess`.
    """
    if current_user.role not in FARM_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    return current_user


def get_farm_access(
    db: Session = Depends(get_db),
    current_user=Depends(require_farm_role),
) -> FarmAccess:
    """
    Alcance del usuario actual sobre las fincas.

    Los servicios de cada recurso lo usan para resolver la finca raíz de lo
    que consultan (finca, lote, empleado…) y responder 404 fuera de alcance.
    """
    return FarmAccess(db, current_user)
