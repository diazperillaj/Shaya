from fastapi import APIRouter, Depends

from app.farm_operations.api.v1.dependencies import require_farm_role

"""
Router principal del módulo de cultivo.

Compone los routers de cada recurso del módulo (fincas, lotes, ciclos…).
Se monta en `api_v1.py` bajo el prefijo `/farm`; cada sub-router define su
propio prefijo y su etiqueta para Swagger (`farm-plots`, `farm-harvests`…).

El control de acceso del módulo se declara aquí, una sola vez: todas sus
rutas exigen el rol `admin` o `farmer`.
"""

farm_router = APIRouter(dependencies=[Depends(require_farm_role)])
