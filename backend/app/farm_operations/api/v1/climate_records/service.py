from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError, NotFoundError
from app.farm_operations.api.v1.climate_records.schema import ClimateRecordCreate, ClimateRecordUpdate
from app.farm_operations.models import ClimateRecord
from app.farm_operations.models.enums import PlotStatusEnum
from app.farm_operations.services.access import FarmAccess

FIELDS = ("record_date", "rainfall_mm", "temp_min_c", "temp_max_c")


class ClimateRecordService:
    """
    Clima registrado a mano en la finca.

    Un registro sin lote aplica a toda la finca; con lote, solo a ese lote.
    Se cruza con los ciclos por fecha al consultar (modelo-datos §3.6).
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_records(
        self,
        farm_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[dict]:
        query = self.access.farm_records(ClimateRecord)
        if farm_id is not None:
            query = query.filter(ClimateRecord.farm_id == farm_id)
        if plot_id is not None:
            query = query.filter(ClimateRecord.plot_id == plot_id)
        if date_from is not None:
            query = query.filter(ClimateRecord.record_date >= date_from)
        if date_to is not None:
            query = query.filter(ClimateRecord.record_date <= date_to)
        records = query.order_by(ClimateRecord.record_date.desc(), ClimateRecord.id.desc()).all()
        return [self._to_response(record) for record in records]

    def create(self, payload: ClimateRecordCreate) -> dict:
        farm = self.access.get_farm(payload.farm_id)
        self._validate_plot(farm.id, payload.plot_id)
        record = ClimateRecord(farm_id=farm.id, plot_id=payload.plot_id, **self._fields(payload))
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def update(self, record_id: int, payload: ClimateRecordUpdate) -> dict:
        record = self._get(record_id)
        if payload.plot_id != record.plot_id:
            self._validate_plot(record.farm_id, payload.plot_id)
        record.plot_id = payload.plot_id
        for field, value in self._fields(payload).items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def delete(self, record_id: int) -> None:
        record = self._get(record_id)
        self.db.delete(record)
        self.db.commit()

    def _get(self, record_id: int) -> ClimateRecord:
        record = self.access.farm_records(ClimateRecord).filter(ClimateRecord.id == record_id).first()
        if not record:
            raise NotFoundError("Registro no encontrado")
        return record

    def _validate_plot(self, farm_id: int, plot_id: Optional[int]) -> None:
        if plot_id is None:
            return
        plot = self.access.get_plot(plot_id)
        if plot.farm_id != farm_id:
            raise ConflictError("El lote no es de esta finca")
        if plot.status == PlotStatusEnum.closed:
            raise ConflictError(f"El lote «{plot.name}» está cerrado: no admite registros nuevos")

    @staticmethod
    def _fields(payload: ClimateRecordUpdate) -> dict:
        return {
            **{field: getattr(payload, field) for field in FIELDS},
            "observations": (payload.observations or "").strip() or None,
        }

    @staticmethod
    def _to_response(record: ClimateRecord) -> dict:
        return {
            "id": record.id,
            "farm_id": record.farm_id,
            "plot_id": record.plot_id,
            "plot_name": record.plot.name if record.plot else None,
            **{field: getattr(record, field) for field in FIELDS},
            "observations": record.observations,
            "created_at": record.created_at,
        }
