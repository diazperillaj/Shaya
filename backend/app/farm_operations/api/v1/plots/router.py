from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.plots.schema import (
    PlotCloseRequest,
    PlotCreate,
    PlotEventCreate,
    PlotEventResponse,
    PlotReopenRequest,
    PlotResponse,
    PlotUpdate,
    RenewalDefaults,
)
from app.farm_operations.api.v1.plots.service import PlotService
from app.farm_operations.api.v1.quality_projection.schema import QualityProjectionResponse
from app.farm_operations.api.v1.quality_projection.service import ProjectionService
from app.farm_operations.models.enums import PlotStatusEnum
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> PlotService:
    return PlotService(db, access)


@router.post("/create", response_model=PlotResponse)
def create_plot(payload: PlotCreate, service: PlotService = Depends(get_service)):
    """Crea un lote. Con `renewed_from_plot_id`, vuelve a sembrar el terreno de un lote cerrado."""
    return service.create_plot(payload)


@router.get("/get", response_model=List[PlotResponse])
def get_plots(
    farm_id: Optional[int] = Query(None),
    status: Optional[PlotStatusEnum] = Query(None),
    variety: Optional[str] = Query(None),
    service: PlotService = Depends(get_service),
):
    return service.get_plots(farm_id=farm_id, status=status, variety=variety)


@router.get("/get/{plot_id}", response_model=PlotResponse)
def get_plot(plot_id: int, service: PlotService = Depends(get_service)):
    """Detalle del lote con su edad efectiva."""
    return service.get_plot(plot_id)


@router.get("/get/{plot_id}/renewal-defaults", response_model=RenewalDefaults)
def get_renewal_defaults(plot_id: int, service: PlotService = Depends(get_service)):
    """Datos del terreno para precargar el formulario del lote que lo renueva."""
    return service.get_renewal_defaults(plot_id)


@router.put("/update/{plot_id}", response_model=PlotResponse)
def update_plot(plot_id: int, payload: PlotUpdate, service: PlotService = Depends(get_service)):
    return service.update_plot(plot_id, payload)


@router.post("/{plot_id}/close", response_model=PlotResponse)
def close_plot(plot_id: int, payload: PlotCloseRequest, service: PlotService = Depends(get_service)):
    """Cierre definitivo del lote: dejó de dar cosecha."""
    return service.close_plot(plot_id, payload)


@router.post("/{plot_id}/reopen", response_model=PlotResponse)
def reopen_plot(plot_id: int, payload: PlotReopenRequest, service: PlotService = Depends(get_service)):
    """Corrige un cierre hecho por error."""
    return service.reopen_plot(plot_id, payload)


@router.delete("/delete/{plot_id}", response_model=dict)
def delete_plot(plot_id: int, service: PlotService = Depends(get_service)):
    """Elimina un lote sin historial."""
    service.delete_plot(plot_id)
    return {"message": f"Lote {plot_id} eliminado exitosamente"}


@router.post("/{plot_id}/events/create", response_model=PlotEventResponse)
def create_plot_event(plot_id: int, payload: PlotEventCreate, service: PlotService = Depends(get_service)):
    """Registra un evento manual: zoca, resiembra parcial, cambio de sombrío u otro."""
    return service.create_event(plot_id, payload)


@router.get("/{plot_id}/events/get", response_model=List[PlotEventResponse])
def get_plot_events(plot_id: int, service: PlotService = Depends(get_service)):
    """Historial de eventos del lote, del más reciente al más antiguo."""
    return service.get_events(plot_id)


@router.get("/{plot_id}/quality-projection", response_model=QualityProjectionResponse)
def get_quality_projection(
    plot_id: int,
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
):
    """Proyección de calidad del ciclo activo del lote (409 sin ciclo activo; 503 sin modelo)."""
    return ProjectionService(db, access).for_plot(plot_id)
