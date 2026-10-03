from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.quality_evals.schema import (
    QualityEvalCreate,
    QualityEvalResponse,
    QualityEvalUpdate,
)
from app.farm_operations.api.v1.quality_evals.service import QualityEvalService
from app.farm_operations.models.enums import QualityStageEnum
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> QualityEvalService:
    return QualityEvalService(db, access)


@router.post("/create", response_model=QualityEvalResponse)
def create(payload: QualityEvalCreate, service: QualityEvalService = Depends(get_service)):
    """Registra una evaluación en cereza (de una cosecha) o en pergamino (de un secado)."""
    return service.create(payload)


@router.get("/get", response_model=List[QualityEvalResponse])
def get_list(
    stage: Optional[QualityStageEnum] = Query(None),
    harvest_id: Optional[int] = Query(None),
    drying_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: QualityEvalService = Depends(get_service),
):
    return service.get_list(
        stage=stage, harvest_id=harvest_id, drying_id=drying_id, date_from=date_from, date_to=date_to,
    )


@router.put("/update/{eval_id}", response_model=QualityEvalResponse)
def update(eval_id: int, payload: QualityEvalUpdate, service: QualityEvalService = Depends(get_service)):
    """Corrige los resultados; la etapa y su cosecha o secado no cambian."""
    return service.update(eval_id, payload)


@router.delete("/delete/{eval_id}", response_model=dict)
def delete(eval_id: int, service: QualityEvalService = Depends(get_service)):
    service.delete(eval_id)
    return {"message": f"Evaluación {eval_id} eliminada exitosamente"}
