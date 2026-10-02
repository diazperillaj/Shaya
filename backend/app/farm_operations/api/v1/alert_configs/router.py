from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.alert_configs.schema import (
    AlertConfigValues,
    ResolvedAlertConfig,
)
from app.farm_operations.api.v1.alert_configs.service import AlertConfigService
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> AlertConfigService:
    return AlertConfigService(db, access)


@router.get("/resolved/farm/{farm_id}", response_model=ResolvedAlertConfig)
def get_farm_config(farm_id: int, service: AlertConfigService = Depends(get_service)):
    """Configuración efectiva de la finca (finca → valor por defecto)."""
    return service.resolved_for_farm(farm_id)


@router.get("/resolved/plot/{plot_id}", response_model=ResolvedAlertConfig)
def get_plot_config(plot_id: int, service: AlertConfigService = Depends(get_service)):
    """Configuración efectiva del lote (lote → finca → valor por defecto)."""
    return service.resolved_for_plot(plot_id)


@router.put("/farm/{farm_id}", response_model=ResolvedAlertConfig)
def save_farm_config(
    farm_id: int,
    payload: AlertConfigValues,
    service: AlertConfigService = Depends(get_service),
):
    """Reemplaza la configuración de la finca; los valores en null usan el valor por defecto."""
    return service.save_for_farm(farm_id, payload)


@router.put("/plot/{plot_id}", response_model=ResolvedAlertConfig)
def save_plot_config(
    plot_id: int,
    payload: AlertConfigValues,
    service: AlertConfigService = Depends(get_service),
):
    """Reemplaza el override del lote; los valores en null heredan de la finca."""
    return service.save_for_plot(plot_id, payload)


@router.delete("/plot/{plot_id}", response_model=dict)
def delete_plot_config(plot_id: int, service: AlertConfigService = Depends(get_service)):
    """Quita el override del lote: vuelve a heredar de la finca."""
    service.delete_for_plot(plot_id)
    return {"message": f"El lote {plot_id} vuelve a usar la configuración de la finca"}
