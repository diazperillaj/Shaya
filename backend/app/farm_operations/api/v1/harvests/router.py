from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.harvests.schema import (
    HarvestCloseRequest,
    HarvestCreate,
    HarvestDetail,
    HarvestResponse,
    HarvestUpdate,
    HarvestWorkFields,
    HarvestWorkResponse,
)
from app.farm_operations.api.v1.harvests.service import HarvestService
from app.farm_operations.models.enums import HarvestStatusEnum
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> HarvestService:
    return HarvestService(db, access)


# ── Cosechas ──────────────────────────────────────────────────────────────


@router.post("/create", response_model=HarvestDetail)
def create_harvest(payload: HarvestCreate, service: HarvestService = Depends(get_service)):
    """Abre una pasada de cosecha en un ciclo activo; `pass_number` lo asigna el servicio."""
    return service.create_harvest(payload)


@router.get("/get", response_model=List[HarvestResponse])
def get_harvests(
    crop_cycle_id: Optional[int] = Query(None),
    plot_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    status: Optional[HarvestStatusEnum] = Query(None),
    service: HarvestService = Depends(get_service),
):
    return service.get_harvests(crop_cycle_id=crop_cycle_id, plot_id=plot_id, farm_id=farm_id, status=status)


@router.get("/get/{harvest_id}", response_model=HarvestDetail)
def get_harvest(harvest_id: int, service: HarvestService = Depends(get_service)):
    """Detalle de la cosecha con su recolección y los totales acumulados."""
    return service.get_harvest(harvest_id)


@router.put("/update/{harvest_id}", response_model=HarvestDetail)
def update_harvest(harvest_id: int, payload: HarvestUpdate, service: HarvestService = Depends(get_service)):
    """Corrige fechas, tarifas por defecto y observaciones; fin y total solo en cosechas cerradas."""
    return service.update_harvest(harvest_id, payload)


@router.post("/{harvest_id}/close", response_model=HarvestDetail)
def close_harvest(harvest_id: int, payload: HarvestCloseRequest, service: HarvestService = Depends(get_service)):
    """Cierra la sesión con su total de café cereza (por defecto, la suma de los kg registrados)."""
    return service.close_harvest(harvest_id, payload)


@router.post("/{harvest_id}/reopen", response_model=HarvestDetail)
def reopen_harvest(harvest_id: int, service: HarvestService = Depends(get_service)):
    """Corrige un cierre hecho por error (solo la última pasada de un ciclo activo)."""
    return service.reopen_harvest(harvest_id)


@router.delete("/delete/{harvest_id}", response_model=dict)
def delete_harvest(harvest_id: int, service: HarvestService = Depends(get_service)):
    """Elimina una cosecha sin recolección."""
    service.delete_harvest(harvest_id)
    return {"message": f"Cosecha {harvest_id} eliminada exitosamente"}


# ── Recolección diaria ────────────────────────────────────────────────────


@router.post("/{harvest_id}/works/create", response_model=HarvestWorkResponse)
def create_work(harvest_id: int, payload: HarvestWorkFields, service: HarvestService = Depends(get_service)):
    """Registra la recolección de un empleado en un día, al peso o por jornal."""
    return service.create_work(harvest_id, payload)


@router.get("/{harvest_id}/works/get", response_model=List[HarvestWorkResponse])
def get_works(
    harvest_id: int,
    employee_id: Optional[int] = Query(None),
    paid: Optional[bool] = Query(None),
    service: HarvestService = Depends(get_service),
):
    return service.get_works(harvest_id, employee_id=employee_id, paid=paid)


@router.put("/works/update/{work_id}", response_model=HarvestWorkResponse)
def update_work(work_id: int, payload: HarvestWorkFields, service: HarvestService = Depends(get_service)):
    """Corrige un registro sin pagar de una cosecha abierta."""
    return service.update_work(work_id, payload)


@router.delete("/works/delete/{work_id}", response_model=dict)
def delete_work(work_id: int, service: HarvestService = Depends(get_service)):
    """Elimina un registro sin pagar de una cosecha abierta."""
    service.delete_work(work_id)
    return {"message": f"Registro {work_id} eliminado exitosamente"}
