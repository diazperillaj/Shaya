from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.soil_analyses.schema import (
    SoilAnalysisCreate,
    SoilAnalysisResponse,
    SoilAnalysisUpdate,
)
from app.farm_operations.api.v1.soil_analyses.service import SoilAnalysisService
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> SoilAnalysisService:
    return SoilAnalysisService(db, access)


@router.post("/create", response_model=SoilAnalysisResponse)
def create_analysis(payload: SoilAnalysisCreate, service: SoilAnalysisService = Depends(get_service)):
    """Registra un análisis de suelo del lote."""
    return service.create(payload)


@router.get("/get", response_model=List[SoilAnalysisResponse])
def get_analyses(
    plot_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: SoilAnalysisService = Depends(get_service),
):
    return service.get_records(plot_id=plot_id, farm_id=farm_id, date_from=date_from, date_to=date_to)


@router.put("/update/{record_id}", response_model=SoilAnalysisResponse)
def update_analysis(record_id: int, payload: SoilAnalysisUpdate, service: SoilAnalysisService = Depends(get_service)):
    return service.update(record_id, payload)


@router.delete("/delete/{record_id}", response_model=dict)
def delete_analysis(record_id: int, service: SoilAnalysisService = Depends(get_service)):
    service.delete(record_id)
    return {"message": f"Registro {record_id} eliminado exitosamente"}
