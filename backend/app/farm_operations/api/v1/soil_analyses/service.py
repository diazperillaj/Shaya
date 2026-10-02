from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError, NotFoundError
from app.farm_operations.api.v1.soil_analyses.schema import SoilAnalysisCreate, SoilAnalysisUpdate
from app.farm_operations.models import Plot, SoilAnalysis
from app.farm_operations.models.enums import PlotStatusEnum
from app.farm_operations.services.access import FarmAccess

FIELDS = (
    "analysis_date", "ph", "organic_matter_pct", "nitrogen", "phosphorus", "potassium",
)
TEXTS = ("texture", "laboratory", "observations")


class SoilAnalysisService:
    """
    Análisis de suelo de un lote.

    Cuelga del lote y no del ciclo porque el suelo es del terreno; puede ser
    anterior a la siembra (se suele analizar antes de sembrar).
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_records(
        self,
        plot_id: Optional[int] = None,
        farm_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[dict]:
        query = self.access.plot_records(SoilAnalysis)
        if plot_id is not None:
            query = query.filter(SoilAnalysis.plot_id == plot_id)
        if farm_id is not None:
            query = query.filter(Plot.farm_id == farm_id)
        if date_from is not None:
            query = query.filter(SoilAnalysis.analysis_date >= date_from)
        if date_to is not None:
            query = query.filter(SoilAnalysis.analysis_date <= date_to)
        records = query.order_by(SoilAnalysis.analysis_date.desc(), SoilAnalysis.id.desc()).all()
        return [self._to_response(record) for record in records]

    def create(self, payload: SoilAnalysisCreate) -> dict:
        plot = self.access.get_plot(payload.plot_id)
        if plot.status == PlotStatusEnum.closed:
            raise ConflictError(f"El lote «{plot.name}» está cerrado: no admite registros nuevos")
        record = SoilAnalysis(plot_id=plot.id, **self._fields(payload))
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def update(self, record_id: int, payload: SoilAnalysisUpdate) -> dict:
        record = self._get(record_id)
        for field, value in self._fields(payload).items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def delete(self, record_id: int) -> None:
        record = self._get(record_id)
        self.db.delete(record)
        self.db.commit()

    def _get(self, record_id: int) -> SoilAnalysis:
        record = self.access.plot_records(SoilAnalysis).filter(SoilAnalysis.id == record_id).first()
        if not record:
            raise NotFoundError("Registro no encontrado")
        return record

    @staticmethod
    def _fields(payload: SoilAnalysisUpdate) -> dict:
        return {
            **{field: getattr(payload, field) for field in FIELDS},
            **{field: (getattr(payload, field) or "").strip() or None for field in TEXTS},
        }

    @staticmethod
    def _to_response(record: SoilAnalysis) -> dict:
        return {
            "id": record.id,
            "plot_id": record.plot_id,
            "plot_name": record.plot.name,
            **{field: getattr(record, field) for field in FIELDS + TEXTS},
            "created_at": record.created_at,
        }
