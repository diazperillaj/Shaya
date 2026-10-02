from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import require_admin
from app.core.db.session import get_db
from app.farm_operations.api.v1.supplies.schema import (
    SupplyCreate,
    SupplyResponse,
    SupplyUpdate,
)
from app.farm_operations.api.v1.supplies.service import SupplyService
from app.farm_operations.models.enums import SupplyTypeEnum

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> SupplyService:
    return SupplyService(db)


@router.post("/create", response_model=SupplyResponse)
def create_supply(payload: SupplyCreate, service: SupplyService = Depends(get_service)):
    """Agrega un insumo al catálogo; también se usa al vuelo desde los formularios de labores."""
    return service.create_supply(payload)


@router.get("/get", response_model=List[SupplyResponse])
def get_supplies(
    supply_type: Optional[SupplyTypeEnum] = Query(None),
    search: Optional[str] = Query(None, description="Nombre o composición"),
    active: Optional[bool] = Query(None),
    service: SupplyService = Depends(get_service),
):
    return service.get_supplies(supply_type=supply_type, search=search, active=active)


@router.put("/update/{supply_id}", response_model=SupplyResponse)
def update_supply(supply_id: int, payload: SupplyUpdate, service: SupplyService = Depends(get_service)):
    return service.update_supply(supply_id, payload)


@router.post("/{supply_id}/deactivate", response_model=SupplyResponse, dependencies=[Depends(require_admin)])
def deactivate_supply(supply_id: int, service: SupplyService = Depends(get_service)):
    """Oculta el insumo de los formularios sin borrar su historial."""
    return service.set_active(supply_id, False)


@router.post("/{supply_id}/activate", response_model=SupplyResponse, dependencies=[Depends(require_admin)])
def activate_supply(supply_id: int, service: SupplyService = Depends(get_service)):
    return service.set_active(supply_id, True)


@router.delete("/delete/{supply_id}", response_model=dict, dependencies=[Depends(require_admin)])
def delete_supply(supply_id: int, service: SupplyService = Depends(get_service)):
    """Elimina un insumo que ninguna labor usa."""
    service.delete_supply(supply_id)
    return {"message": f"Insumo {supply_id} eliminado exitosamente"}
