from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.api.v1.validation import clean_other_detail
from app.farm_operations.api.v1.wet_processings.schema import (
    WetCompleteRequest,
    WetInputItem,
    WetInputsReplace,
    WetProcessingCreate,
    WetProcessingStages,
    WetProcessingUpdate,
)
from app.farm_operations.models import DryingInput, WetProcessing, WetProcessingInput
from app.farm_operations.models.enums import FermentationMethodEnum, WetProcessingStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.mass_balance import check_harvest_inputs, cherry_in, kg, wet_dried_kg

STAGE_FIELDS = (
    "floats_kg", "floats_method", "pulped_at",
    "fermentation_start", "fermentation_end", "fermentation_method",
    "fermentation_decided_by", "fermentation_criteria", "ambient_temp_c",
    "wash_count", "washed_kg", "observations",
)
TEXT_FIELDS = ("floats_method", "fermentation_decided_by", "fermentation_criteria", "observations")
SECONDS_PER_HOUR = Decimal(3600)


class WetProcessingService:
    """
    Beneficio húmedo: recibe café cereza de cosechas de la finca y registra
    sus etapas a medida que ocurren. Al completarse queda fijo su café
    lavado, que es lo que se reparte en secados.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_list(self, farm_id: Optional[int] = None, status: Optional[WetProcessingStatusEnum] = None) -> List[dict]:
        query = self.access.farm_records(WetProcessing)
        if farm_id is not None:
            query = query.filter(WetProcessing.farm_id == farm_id)
        if status is not None:
            query = query.filter(WetProcessing.status == status)
        records = query.order_by(WetProcessing.created_at.desc(), WetProcessing.id.desc()).all()
        return [self._to_response(record) for record in records]

    def get_one(self, wet_processing_id: int) -> dict:
        return self._to_response(self.access.get_wet_processing(wet_processing_id))

    # ── Escritura ─────────────────────────────────────────────────────────

    def create(self, payload: WetProcessingCreate) -> dict:
        farm = self.access.get_farm(payload.farm_id)
        record = WetProcessing(farm_id=farm.id)
        self._set_stages(record, payload)
        record.inputs = self._build_inputs(farm.id, payload.inputs)
        self._check_washed(record)
        self.db.add(record)
        self.db.commit()
        return self.get_one(record.id)

    def update(self, wet_processing_id: int, payload: WetProcessingUpdate) -> dict:
        record = self._get_in_progress(wet_processing_id)
        self._set_stages(record, payload)
        self._check_washed(record)
        self.db.commit()
        return self.get_one(record.id)

    def replace_inputs(self, wet_processing_id: int, payload: WetInputsReplace) -> dict:
        record = self._get_in_progress(wet_processing_id)
        new_inputs = self._build_inputs(record.farm_id, payload.inputs, exclude_wet_processing_id=record.id)
        record.inputs = []
        self.db.flush()  # los aportes viejos se borran antes de insertar los nuevos (único por cosecha)
        record.inputs = new_inputs
        self._check_washed(record)
        self.db.commit()
        return self.get_one(record.id)

    def complete(self, wet_processing_id: int, payload: WetCompleteRequest) -> dict:
        """Completa el beneficio: su café lavado queda fijo para repartirlo en secados."""
        record = self._get_in_progress(wet_processing_id)
        if payload.washed_kg is not None:
            record.washed_kg = payload.washed_kg
        if record.washed_kg is None:
            raise ConflictError("Indica los kg de café lavado para completar el beneficio")
        self._check_washed(record)
        record.status = WetProcessingStatusEnum.completed
        self.db.commit()
        return self.get_one(record.id)

    def reopen(self, wet_processing_id: int) -> dict:
        """Corrige un beneficio completado por error, si su café aún no se secó."""
        record = self.access.get_wet_processing(wet_processing_id)
        if record.status == WetProcessingStatusEnum.in_progress:
            raise ConflictError("El beneficio ya está en curso")
        if self._has_dryings(record.id):
            raise ConflictError("No se puede reabrir: su café lavado ya está en un secado")
        record.status = WetProcessingStatusEnum.in_progress
        self.db.commit()
        return self.get_one(record.id)

    def delete(self, wet_processing_id: int) -> None:
        record = self.access.get_wet_processing(wet_processing_id)
        if self._has_dryings(record.id):
            raise ConflictError("No se puede eliminar: su café lavado ya está en un secado")
        self.db.delete(record)
        self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    def _get_in_progress(self, wet_processing_id: int) -> WetProcessing:
        record = self.access.get_wet_processing(wet_processing_id)
        if record.status != WetProcessingStatusEnum.in_progress:
            raise ConflictError("El beneficio está completado: reábrelo para corregirlo")
        return record

    def _has_dryings(self, wet_processing_id: int) -> bool:
        return self.db.query(DryingInput.id).filter(DryingInput.wet_processing_id == wet_processing_id).first() is not None

    def _build_inputs(
        self,
        farm_id: int,
        items: List[WetInputItem],
        exclude_wet_processing_id: Optional[int] = None,
    ) -> List[WetProcessingInput]:
        """Aportes de cosechas de la misma finca, dentro de su balance de masas."""
        pairs = []
        for item in items:
            harvest = self.access.get_harvest(item.harvest_id)
            if harvest.crop_cycle.plot.farm_id != farm_id:
                raise ConflictError("Todas las cosechas deben ser de la finca del beneficio")
            pairs.append((harvest, item.cherry_kg))
        check_harvest_inputs(self.db, pairs, exclude_wet_processing_id)
        return [WetProcessingInput(harvest_id=harvest.id, cherry_kg=cherry_kg) for harvest, cherry_kg in pairs]

    @staticmethod
    def _check_washed(record: WetProcessing) -> None:
        """No sale más café lavado que la cereza que entró."""
        cherry = cherry_in(record)
        if record.washed_kg is not None and record.washed_kg > cherry:
            raise ConflictError(
                f"El café lavado ({kg(record.washed_kg)}) no puede superar la cereza que entró ({kg(cherry)})"
            )

    @staticmethod
    def _set_stages(record: WetProcessing, payload: WetProcessingStages) -> None:
        for field in STAGE_FIELDS:
            value = getattr(payload, field)
            if field in TEXT_FIELDS:
                value = (value or "").strip() or None
            setattr(record, field, value)
        record.fermentation_other_detail = clean_other_detail(
            payload.fermentation_method == FermentationMethodEnum.other, payload.fermentation_other_detail
        )

    def _to_response(self, record: WetProcessing) -> dict:
        hours = None
        if record.fermentation_start and record.fermentation_end:
            seconds = Decimal((record.fermentation_end - record.fermentation_start).total_seconds())
            hours = (seconds / SECONDS_PER_HOUR).quantize(Decimal("0.1"))
        return {
            **{field: getattr(record, field) for field in STAGE_FIELDS},
            "id": record.id,
            "farm_id": record.farm_id,
            "farm_name": record.farm.name,
            "status": record.status,
            "fermentation_other_detail": record.fermentation_other_detail,
            "created_at": record.created_at,
            "cherry_kg": cherry_in(record),
            "fermentation_hours": hours,
            "washed_kg_dried": wet_dried_kg(self.db, record.id),
            "inputs": [
                {
                    "harvest_id": item.harvest_id,
                    "cherry_kg": item.cherry_kg,
                    "plot_id": item.harvest.crop_cycle.plot_id,
                    "plot_name": item.harvest.crop_cycle.plot.name,
                    "cycle_number": item.harvest.crop_cycle.cycle_number,
                    "pass_number": item.harvest.pass_number,
                    "harvest_status": item.harvest.status,
                }
                for item in record.inputs
            ],
        }
