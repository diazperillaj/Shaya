from fastapi import APIRouter, Depends

from app.farm_operations.api.v1.alert_configs import router as alert_configs_router
from app.farm_operations.api.v1.dependencies import require_farm_role
from app.farm_operations.api.v1.employees import router as employees_router
from app.farm_operations.api.v1.farmer_accounts import router as farmer_accounts_router
from app.farm_operations.api.v1.farms import router as farms_router
from app.farm_operations.api.v1.plots import router as plots_router
from app.farm_operations.api.v1.supplies import router as supplies_router

"""
Router principal del módulo de cultivo.

Compone los routers de cada recurso del módulo (fincas, lotes, ciclos…).
Se monta en `api_v1.py` bajo el prefijo `/farm`; cada sub-router define su
propio prefijo y su etiqueta para Swagger (`farm-plots`, `farm-harvests`…).

El control de acceso del módulo se declara aquí, una sola vez: todas sus
rutas exigen el rol `admin` o `farmer`.
"""

farm_router = APIRouter(dependencies=[Depends(require_farm_role)])

farm_router.include_router(farms_router.router, prefix="/farms", tags=["farm-farms"])
farm_router.include_router(plots_router.router, prefix="/plots", tags=["farm-plots"])
farm_router.include_router(alert_configs_router.router, prefix="/alert-configs", tags=["farm-alert-configs"])
farm_router.include_router(supplies_router.router, prefix="/supplies", tags=["farm-supplies"])
farm_router.include_router(employees_router.router, prefix="/employees", tags=["farm-employees"])
farm_router.include_router(farmer_accounts_router.router, prefix="/farmer-accounts", tags=["farm-farmer-accounts"])
