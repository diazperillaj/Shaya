from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.farms.schema import FarmCreate, FarmResponse, FarmUpdate
from app.farm_operations.api.v1.farms.service import FarmService
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> FarmService:
    return FarmService(db, access)


@router.post("/create", response_model=FarmResponse)
def create_farm(payload: FarmCreate, service: FarmService = Depends(get_service)):
    """Crea una finca. El administrador indica el caficultor; un caficultor la registra a su nombre."""
    return service.create_farm(payload)


@router.get("/get", response_model=List[FarmResponse])
def get_farms(
    search: Optional[str] = Query(None, description="Nombre, vereda o municipio"),
    active: Optional[bool] = Query(None),
    service: FarmService = Depends(get_service),
):
    """Fincas visibles para el usuario, con su cantidad de lotes activos."""
    return service.get_farms(search=search, active=active)


@router.get("/get/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: int, service: FarmService = Depends(get_service)):
    return service.get_farm(farm_id)


@router.put("/update/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, payload: FarmUpdate, service: FarmService = Depends(get_service)):
    return service.update_farm(farm_id, payload)


@router.delete("/delete/{farm_id}", response_model=dict)
def delete_farm(farm_id: int, service: FarmService = Depends(get_service)):
    """Elimina una finca sin lotes ni empleados."""
    service.delete_farm(farm_id)
    return {"message": f"Finca {farm_id} eliminada exitosamente"}
