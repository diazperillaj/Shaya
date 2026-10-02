from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.crop_cycles.schema import (
    CycleCloseRequest,
    CycleCreate,
    CycleDetail,
    CycleResponse,
    CycleUpdate,
)
from app.farm_operations.api.v1.crop_cycles.service import CropCycleService
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.models.enums import CycleStatusEnum
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> CropCycleService:
    return CropCycleService(db, access)


@router.post("/create", response_model=CycleDetail)
def create_cycle(payload: CycleCreate, service: CropCycleService = Depends(get_service)):
    """Abre un ciclo en un lote activo que no tenga otro ciclo activo."""
    return service.create_cycle(payload)


@router.get("/get", response_model=List[CycleResponse])
def get_cycles(
    plot_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    status: Optional[CycleStatusEnum] = Query(None),
    service: CropCycleService = Depends(get_service),
):
    return service.get_cycles(plot_id=plot_id, farm_id=farm_id, status=status)


@router.get("/get/{cycle_id}", response_model=CycleDetail)
def get_cycle(cycle_id: int, service: CropCycleService = Depends(get_service)):
    """Detalle del ciclo con el resumen de sus labores por tipo."""
    return service.get_cycle(cycle_id)


@router.put("/update/{cycle_id}", response_model=CycleDetail)
def update_cycle(cycle_id: int, payload: CycleUpdate, service: CropCycleService = Depends(get_service)):
    """Corrige fechas u observaciones; la fecha de fin solo en ciclos cerrados."""
    return service.update_cycle(cycle_id, payload)


@router.post("/{cycle_id}/close", response_model=CycleDetail)
def close_cycle(cycle_id: int, payload: CycleCloseRequest, service: CropCycleService = Depends(get_service)):
    """Cierra el ciclo al terminar su cosecha."""
    return service.close_cycle(cycle_id, payload)


@router.post("/{cycle_id}/reopen", response_model=CycleDetail)
def reopen_cycle(cycle_id: int, service: CropCycleService = Depends(get_service)):
    """Corrige un cierre hecho por error (solo el último ciclo del lote)."""
    return service.reopen_cycle(cycle_id)


@router.delete("/delete/{cycle_id}", response_model=dict)
def delete_cycle(cycle_id: int, service: CropCycleService = Depends(get_service)):
    """Elimina un ciclo sin labores."""
    service.delete_cycle(cycle_id)
    return {"message": f"Ciclo {cycle_id} eliminado exitosamente"}
