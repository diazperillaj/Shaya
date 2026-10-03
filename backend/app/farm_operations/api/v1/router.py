from fastapi import APIRouter, Depends

from app.farm_operations.api.v1.alert_configs import router as alert_configs_router
from app.farm_operations.api.v1.climate_records import router as climate_records_router
from app.farm_operations.api.v1.crop_cycles import router as crop_cycles_router
from app.farm_operations.api.v1.day_labors import router as day_labors_router
from app.farm_operations.api.v1.dependencies import require_farm_role
from app.farm_operations.api.v1.employees import router as employees_router
from app.farm_operations.api.v1.farmer_accounts import router as farmer_accounts_router
from app.farm_operations.api.v1.farms import router as farms_router
from app.farm_operations.api.v1.harvests import router as harvests_router
from app.farm_operations.api.v1.labors.kinds import LABOR_KINDS
from app.farm_operations.api.v1.labors.router import build_router as build_labor_router
from app.farm_operations.api.v1.payments import router as payments_router
from app.farm_operations.api.v1.plots import router as plots_router
from app.farm_operations.api.v1.soil_analyses import router as soil_analyses_router
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
farm_router.include_router(crop_cycles_router.router, prefix="/crop-cycles", tags=["farm-crop-cycles"])
for kind in LABOR_KINDS:
    farm_router.include_router(build_labor_router(kind), prefix=f"/{kind.path}", tags=[f"farm-{kind.path}"])
farm_router.include_router(soil_analyses_router.router, prefix="/soil-analyses", tags=["farm-soil-analyses"])
farm_router.include_router(climate_records_router.router, prefix="/climate-records", tags=["farm-climate-records"])
farm_router.include_router(alert_configs_router.router, prefix="/alert-configs", tags=["farm-alert-configs"])
farm_router.include_router(supplies_router.router, prefix="/supplies", tags=["farm-supplies"])
farm_router.include_router(employees_router.router, prefix="/employees", tags=["farm-employees"])
farm_router.include_router(harvests_router.router, prefix="/harvests", tags=["farm-harvests"])
farm_router.include_router(day_labors_router.router, prefix="/day-labors", tags=["farm-day-labors"])
farm_router.include_router(payments_router.router, prefix="/payments", tags=["farm-payments"])
farm_router.include_router(farmer_accounts_router.router, prefix="/farmer-accounts", tags=["farm-farmer-accounts"])
