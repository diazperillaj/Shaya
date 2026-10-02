from fastapi import Depends, HTTPException

from app.api.api_v1.auth.dependencies import get_current_user
from app.core.roles import FARM_ROLES


def require_farm_role(current_user=Depends(get_current_user)):
    """
    Acceso al módulo de cultivo: administradores y caficultores.

    El rol `user` (personal de Shaya) no opera el cultivo y recibe 403. El
    alcance por finca (cada caficultor solo ve las suyas) se aplica en cada
    recurso con `get_accessible_farm`.
    """
    if current_user.role not in FARM_ROLES:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    return current_user
