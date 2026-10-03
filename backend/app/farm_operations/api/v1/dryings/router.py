from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.dryings.schema import (
    DryingCompleteRequest,
    DryingCreate,
    DryingInputsReplace,
    DryingResponse,
    DryingUpdate,
    HumidityCheckCreate,
    InventoryData,
)
from app.farm_operations.api.v1.dryings.service import DryingService
from app.farm_operations.models.enums import DryingDestinationEnum, DryingStatusEnum
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> DryingService:
    return DryingService(db, access)


@router.post("/create", response_model=DryingResponse)
def create(payload: DryingCreate, service: DryingService = Depends(get_service)):
    """Crea el secado con el café lavado que aporta cada beneficio completado de la finca."""
    return service.create(payload)


@router.get("/get", response_model=List[DryingResponse])
def get_list(
    farm_id: Optional[int] = Query(None),
    status: Optional[DryingStatusEnum] = Query(None),
    destination: Optional[DryingDestinationEnum] = Query(None),
    service: DryingService = Depends(get_service),
):
    return service.get_list(farm_id=farm_id, status=status, destination=destination)


@router.get("/get/{drying_id}", response_model=DryingResponse)
def get_one(drying_id: int, service: DryingService = Depends(get_service)):
    """Detalle con aportes, humedad, composición por lote y rendimiento calculado."""
    return service.get_one(drying_id)


@router.put("/update/{drying_id}", response_model=DryingResponse)
def update(drying_id: int, payload: DryingUpdate, service: DryingService = Depends(get_service)):
    """Corrige método, inicio y observaciones (solo en curso)."""
    return service.update(drying_id, payload)


@router.put("/{drying_id}/inputs", response_model=DryingResponse)
def replace_inputs(drying_id: int, payload: DryingInputsReplace, service: DryingService = Depends(get_service)):
    """Reemplaza los aportes de beneficios (solo en curso), revisando el balance de masas."""
    return service.replace_inputs(drying_id, payload)


@router.post("/{drying_id}/humidity-checks/create", response_model=DryingResponse)
def add_humidity_check(drying_id: int, payload: HumidityCheckCreate, service: DryingService = Depends(get_service)):
    """Registra una medición intermedia de humedad."""
    return service.add_humidity_check(drying_id, payload)


@router.delete("/humidity-checks/delete/{check_id}", response_model=DryingResponse)
def delete_humidity_check(check_id: int, service: DryingService = Depends(get_service)):
    return service.delete_humidity_check(check_id)


@router.post("/{drying_id}/complete", response_model=DryingResponse)
def complete(drying_id: int, payload: DryingCompleteRequest, service: DryingService = Depends(get_service)):
    """
    Cierra el secado con su pergamino seco, empaque y destino. Con destino
    inventario, registra el pergamino en la misma transacción.
    """
    return service.complete(drying_id, payload)


@router.post("/{drying_id}/to-inventory", response_model=DryingResponse)
def to_inventory(drying_id: int, payload: InventoryData, service: DryingService = Depends(get_service)):
    """Envía al inventario el pergamino de un secado guardado en la finca."""
    return service.to_inventory(drying_id, payload)


@router.post("/{drying_id}/reopen", response_model=DryingResponse)
def reopen(drying_id: int, service: DryingService = Depends(get_service)):
    """Corrige un cierre hecho por error, si el pergamino no está en el inventario."""
    return service.reopen(drying_id)


@router.delete("/delete/{drying_id}", response_model=dict)
def delete(drying_id: int, service: DryingService = Depends(get_service)):
    """Elimina un secado en curso."""
    service.delete(drying_id)
    return {"message": f"Secado {drying_id} eliminado exitosamente"}
