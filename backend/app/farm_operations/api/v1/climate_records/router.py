from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.climate_records.schema import (
    ClimateRecordCreate,
    ClimateRecordResponse,
    ClimateRecordUpdate,
)
from app.farm_operations.api.v1.climate_records.service import ClimateRecordService
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> ClimateRecordService:
    return ClimateRecordService(db, access)


@router.post("/create", response_model=ClimateRecordResponse)
def create_record(payload: ClimateRecordCreate, service: ClimateRecordService = Depends(get_service)):
    """Registra el clima de un día en la finca o en uno de sus lotes."""
    return service.create(payload)


@router.get("/get", response_model=List[ClimateRecordResponse])
def get_records(
    farm_id: Optional[int] = Query(None),
    plot_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: ClimateRecordService = Depends(get_service),
):
    return service.get_records(farm_id=farm_id, plot_id=plot_id, date_from=date_from, date_to=date_to)


@router.put("/update/{record_id}", response_model=ClimateRecordResponse)
def update_record(
    record_id: int, payload: ClimateRecordUpdate, service: ClimateRecordService = Depends(get_service)
):
    return service.update(record_id, payload)


@router.delete("/delete/{record_id}", response_model=dict)
def delete_record(record_id: int, service: ClimateRecordService = Depends(get_service)):
    service.delete(record_id)
    return {"message": f"Registro {record_id} eliminado exitosamente"}
