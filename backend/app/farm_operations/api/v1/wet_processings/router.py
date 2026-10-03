from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.wet_processings.schema import (
    WetCompleteRequest,
    WetInputsReplace,
    WetProcessingCreate,
    WetProcessingResponse,
    WetProcessingUpdate,
)
from app.farm_operations.api.v1.wet_processings.service import WetProcessingService
from app.farm_operations.models.enums import WetProcessingStatusEnum
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> WetProcessingService:
    return WetProcessingService(db, access)


@router.post("/create", response_model=WetProcessingResponse)
def create(payload: WetProcessingCreate, service: WetProcessingService = Depends(get_service)):
    """Crea el beneficio con el café cereza que aporta cada cosecha de la finca."""
    return service.create(payload)


@router.get("/get", response_model=List[WetProcessingResponse])
def get_list(
    farm_id: Optional[int] = Query(None),
    status: Optional[WetProcessingStatusEnum] = Query(None),
    service: WetProcessingService = Depends(get_service),
):
    return service.get_list(farm_id=farm_id, status=status)


@router.get("/get/{wet_processing_id}", response_model=WetProcessingResponse)
def get_one(wet_processing_id: int, service: WetProcessingService = Depends(get_service)):
    """Detalle con sus aportes, la cereza que entró y las horas de fermentación."""
    return service.get_one(wet_processing_id)


@router.put("/update/{wet_processing_id}", response_model=WetProcessingResponse)
def update(wet_processing_id: int, payload: WetProcessingUpdate, service: WetProcessingService = Depends(get_service)):
    """Registra las etapas a medida que ocurren (solo en curso)."""
    return service.update(wet_processing_id, payload)


@router.put("/{wet_processing_id}/inputs", response_model=WetProcessingResponse)
def replace_inputs(
    wet_processing_id: int, payload: WetInputsReplace, service: WetProcessingService = Depends(get_service)
):
    """Reemplaza los aportes de cosechas (solo en curso), revisando el balance de masas."""
    return service.replace_inputs(wet_processing_id, payload)


@router.post("/{wet_processing_id}/complete", response_model=WetProcessingResponse)
def complete(
    wet_processing_id: int, payload: WetCompleteRequest, service: WetProcessingService = Depends(get_service)
):
    """Completa el beneficio con su café lavado, que queda fijo para los secados."""
    return service.complete(wet_processing_id, payload)


@router.post("/{wet_processing_id}/reopen", response_model=WetProcessingResponse)
def reopen(wet_processing_id: int, service: WetProcessingService = Depends(get_service)):
    """Corrige un beneficio completado por error, si su café aún no se secó."""
    return service.reopen(wet_processing_id)


@router.delete("/delete/{wet_processing_id}", response_model=dict)
def delete(wet_processing_id: int, service: WetProcessingService = Depends(get_service)):
    """Elimina un beneficio cuyo café no se ha secado."""
    service.delete(wet_processing_id)
    return {"message": f"Beneficio {wet_processing_id} eliminado exitosamente"}
