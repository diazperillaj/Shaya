from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import DomainError
from app.farm_operations.api.v1.quality_evals.schema import (
    FIELD_LABELS,
    QualityEvalCreate,
    QualityEvalFields,
    QualityEvalUpdate,
    stage_problem,
)
from app.farm_operations.models import QualityEval
from app.farm_operations.models.enums import QualityStageEnum
from app.farm_operations.services.access import FarmAccess

RESULT_FIELDS = tuple(FIELD_LABELS) + ("eval_date",)


class QualityEvalService:
    """
    Evaluaciones de calidad: en cereza, de una cosecha (composición: maduros,
    verdes, brocados…); en pergamino, de un secado (humedad, defectos,
    factor de rendimiento, puntaje).
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_list(
        self,
        stage: Optional[QualityStageEnum] = None,
        harvest_id: Optional[int] = None,
        drying_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[QualityEval]:
        query = self.access.quality_evals()
        if stage is not None:
            query = query.filter(QualityEval.stage == stage)
        if harvest_id is not None:
            query = query.filter(QualityEval.harvest_id == harvest_id)
        if drying_id is not None:
            query = query.filter(QualityEval.drying_id == drying_id)
        if date_from is not None:
            query = query.filter(QualityEval.eval_date >= date_from)
        if date_to is not None:
            query = query.filter(QualityEval.eval_date <= date_to)
        return query.order_by(QualityEval.eval_date.desc(), QualityEval.id.desc()).all()

    def create(self, payload: QualityEvalCreate) -> QualityEval:
        if payload.harvest_id is not None:
            self.access.get_harvest(payload.harvest_id)
        if payload.drying_id is not None:
            self.access.get_drying(payload.drying_id)
        record = QualityEval(stage=payload.stage, harvest_id=payload.harvest_id, drying_id=payload.drying_id)
        self._set_results(record, payload)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, eval_id: int, payload: QualityEvalUpdate) -> QualityEval:
        record = self.access.get_quality_eval(eval_id)
        problem = stage_problem(record.stage, payload.model_dump())
        if problem:
            raise DomainError(problem)
        self._set_results(record, payload)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, eval_id: int) -> None:
        record = self.access.get_quality_eval(eval_id)
        self.db.delete(record)
        self.db.commit()

    @staticmethod
    def _set_results(record: QualityEval, payload: QualityEvalFields) -> None:
        for field in RESULT_FIELDS:
            setattr(record, field, getattr(payload, field))
        record.observations = (payload.observations or "").strip() or None
