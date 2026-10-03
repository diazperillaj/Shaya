from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError, NotFoundError
from app.farm_operations.api.v1.dryings.schema import (
    DryingCompleteRequest,
    DryingCreate,
    DryingFields,
    DryingInputItem,
    DryingInputsReplace,
    DryingUpdate,
    HumidityCheckCreate,
    InventoryData,
)
from app.farm_operations.api.v1.validation import clean_other_detail
from app.farm_operations.models import AlertConfig, Drying, DryingHumidityCheck, DryingInput, QualityEval
from app.farm_operations.models.enums import DryingDestinationEnum, DryingMethodEnum, DryingStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.alerts import resolve
from app.farm_operations.services.dates import business_today, format_date
from app.farm_operations.services.inventory_bridge import send_to_inventory
from app.farm_operations.services.mass_balance import check_wet_inputs, kg
from app.farm_operations.services.traceability import drying_composition

ZERO = Decimal(0)
COMPLETION_FIELDS = (
    "final_humidity_pct", "output_kg", "packaging", "sack_count", "packed_at", "storage_place", "destination",
)


class DryingService:
    """
    Secado y almacenamiento: recibe café lavado de beneficios completados de
    la finca y, al cerrarse, deja el pergamino seco con su empaque y destino.
    Con destino inventario, el cierre y el registro del pergamino van en una
    sola transacción.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_list(
        self,
        farm_id: Optional[int] = None,
        status: Optional[DryingStatusEnum] = None,
        destination: Optional[DryingDestinationEnum] = None,
    ) -> List[dict]:
        query = self.access.farm_records(Drying)
        if farm_id is not None:
            query = query.filter(Drying.farm_id == farm_id)
        if status is not None:
            query = query.filter(Drying.status == status)
        if destination is not None:
            query = query.filter(Drying.destination == destination)
        records = query.order_by(Drying.start_date.desc(), Drying.id.desc()).all()
        return [self._to_response(record) for record in records]

    def get_one(self, drying_id: int) -> dict:
        return self._to_response(self.access.get_drying(drying_id))

    # ── Secado ────────────────────────────────────────────────────────────

    def create(self, payload: DryingCreate) -> dict:
        farm = self.access.get_farm(payload.farm_id)
        record = Drying(farm_id=farm.id)
        self._set_fields(record, payload)
        record.inputs = self._build_inputs(farm.id, payload.inputs)
        self.db.add(record)
        self.db.commit()
        return self.get_one(record.id)

    def update(self, drying_id: int, payload: DryingUpdate) -> dict:
        record = self._get_in_progress(drying_id)
        first_check = min((check.check_date for check in record.humidity_checks), default=None)
        if first_check is not None and payload.start_date > first_check:
            raise ConflictError(
                f"Hay mediciones de humedad desde el {format_date(first_check)}: el secado no puede empezar después"
            )
        self._set_fields(record, payload)
        self.db.commit()
        return self.get_one(record.id)

    def replace_inputs(self, drying_id: int, payload: DryingInputsReplace) -> dict:
        record = self._get_in_progress(drying_id)
        new_inputs = self._build_inputs(record.farm_id, payload.inputs, exclude_drying_id=record.id)
        record.inputs = []
        self.db.flush()  # los aportes viejos se borran antes de insertar los nuevos (único por beneficio)
        record.inputs = new_inputs
        self.db.commit()
        return self.get_one(record.id)

    def add_humidity_check(self, drying_id: int, payload: HumidityCheckCreate) -> dict:
        record = self._get_in_progress(drying_id)
        if payload.check_date < record.start_date:
            raise ConflictError(f"La medición es anterior al inicio del secado ({format_date(record.start_date)})")
        record.humidity_checks.append(
            DryingHumidityCheck(check_date=payload.check_date, humidity_pct=payload.humidity_pct)
        )
        self.db.commit()
        return self.get_one(record.id)

    def delete_humidity_check(self, check_id: int) -> dict:
        check = self.db.get(DryingHumidityCheck, check_id)
        if check is None:
            raise NotFoundError("Medición no encontrada")
        record = self._get_in_progress(check.drying_id)  # también verifica el alcance
        self.db.delete(check)
        self.db.commit()
        return self.get_one(record.id)

    def complete(self, drying_id: int, payload: DryingCompleteRequest) -> dict:
        """
        Cierra el secado. Con destino inventario registra el pergamino en la
        misma transacción: si eso falla, el secado sigue en curso.
        """
        record = self._get_in_progress(drying_id)
        if payload.end_date < record.start_date:
            raise ConflictError(f"La fecha de fin no puede ser anterior al inicio ({format_date(record.start_date)})")
        last_check = max((check.check_date for check in record.humidity_checks), default=None)
        if last_check is not None and payload.end_date < last_check:
            raise ConflictError(f"Hay mediciones de humedad hasta el {format_date(last_check)}: el secado no puede terminar antes")
        wet_kg = self._wet_kg(record)
        if payload.output_kg > wet_kg:
            raise ConflictError(
                f"El pergamino seco ({kg(payload.output_kg)}) no puede superar el café lavado que entró ({kg(wet_kg)})"
            )

        record.status = DryingStatusEnum.completed
        record.end_date = payload.end_date
        for field in COMPLETION_FIELDS:
            value = getattr(payload, field)
            setattr(record, field, (value.strip() or None) if isinstance(value, str) else value)

        if payload.destination == DryingDestinationEnum.inventory:
            self._to_inventory(record, payload.inventory_data)
        else:
            self.db.commit()
        return self.get_one(record.id)

    def to_inventory(self, drying_id: int, payload: InventoryData) -> dict:
        """Envía al inventario el pergamino de un secado guardado en la finca."""
        record = self.access.get_drying(drying_id)
        if record.status != DryingStatusEnum.completed or record.destination != DryingDestinationEnum.stored:
            raise ConflictError("Solo se envía al inventario el pergamino de un secado cerrado y guardado en la finca")
        record.destination = DryingDestinationEnum.inventory
        self._to_inventory(record, payload)
        return self.get_one(record.id)

    def reopen(self, drying_id: int) -> dict:
        """Corrige un cierre hecho por error, si el pergamino no está en el inventario."""
        record = self.access.get_drying(drying_id)
        if record.status == DryingStatusEnum.in_progress:
            raise ConflictError("El secado ya está en curso")
        if record.parchment is not None:
            raise ConflictError("No se puede reabrir: su pergamino ya está en el inventario")
        record.status = DryingStatusEnum.in_progress
        record.end_date = None
        record.destination = None
        self.db.commit()
        return self.get_one(record.id)

    def delete(self, drying_id: int) -> None:
        record = self.access.get_drying(drying_id)
        if record.status != DryingStatusEnum.in_progress:
            raise ConflictError("Solo se elimina un secado en curso")
        if self.db.query(QualityEval.id).filter(QualityEval.drying_id == record.id).first():
            raise ConflictError("No se puede eliminar: el secado tiene evaluaciones de calidad")
        self.db.delete(record)
        self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    def _get_in_progress(self, drying_id: int) -> Drying:
        record = self.access.get_drying(drying_id)
        if record.status != DryingStatusEnum.in_progress:
            raise ConflictError("El secado está cerrado: reábrelo para corregirlo")
        return record

    def _to_inventory(self, record: Drying, data: InventoryData) -> None:
        if data.purchase_date < record.end_date:
            self.db.rollback()
            raise ConflictError("El ingreso al inventario no puede ser anterior al fin del secado")
        send_to_inventory(self.db, record, data.full_price, data.purchase_date)

    def _build_inputs(
        self,
        farm_id: int,
        items: List[DryingInputItem],
        exclude_drying_id: Optional[int] = None,
    ) -> List[DryingInput]:
        """Aportes de beneficios completados de la misma finca, dentro de su café lavado."""
        pairs = []
        for item in items:
            wet_processing = self.access.get_wet_processing(item.wet_processing_id)
            if wet_processing.farm_id != farm_id:
                raise ConflictError("Todos los beneficios deben ser de la finca del secado")
            pairs.append((wet_processing, item.wet_kg))
        check_wet_inputs(self.db, pairs, exclude_drying_id)
        return [DryingInput(wet_processing_id=wp.id, wet_kg=wet_kg) for wp, wet_kg in pairs]

    @staticmethod
    def _set_fields(record: Drying, payload: DryingFields) -> None:
        record.method = payload.method
        record.other_detail = clean_other_detail(payload.method == DryingMethodEnum.other, payload.other_detail)
        record.start_date = payload.start_date
        record.observations = (payload.observations or "").strip() or None

    @staticmethod
    def _wet_kg(record: Drying) -> Decimal:
        return sum((item.wet_kg for item in record.inputs), ZERO)

    def _humidity_range(self, farm_id: int) -> tuple:
        config = self.db.query(AlertConfig).filter(AlertConfig.farm_id == farm_id).first()
        values = resolve(("farm", config))
        return values["min_final_humidity"]["value"], values["max_final_humidity"]["value"]

    def _to_response(self, record: Drying) -> dict:
        composition = drying_composition(record)
        until = record.end_date or business_today()
        return {
            "id": record.id,
            "farm_id": record.farm_id,
            "farm_name": record.farm.name,
            "status": record.status,
            "method": record.method,
            "other_detail": record.other_detail,
            "start_date": record.start_date,
            "end_date": record.end_date,
            **{field: getattr(record, field) for field in COMPLETION_FIELDS},
            "observations": record.observations,
            "created_at": record.created_at,
            "wet_kg": self._wet_kg(record),
            "days": max((until - record.start_date).days, 0),
            **composition,
            "humidity_range": self._humidity_range(record.farm_id),
            "parchment_id": record.parchment.id if record.parchment else None,
            "inputs": [
                {
                    "wet_processing_id": item.wet_processing_id,
                    "wet_kg": item.wet_kg,
                    "pulped_at": item.wet_processing.pulped_at,
                    "washed_kg": item.wet_processing.washed_kg,
                }
                for item in record.inputs
            ],
            "humidity_checks": [
                {"id": check.id, "check_date": check.check_date, "humidity_pct": check.humidity_pct}
                for check in record.humidity_checks
            ],
        }
