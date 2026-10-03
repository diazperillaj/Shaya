from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError, DomainError
from app.farm_operations.api.v1.harvests.schema import (
    HarvestCloseRequest,
    HarvestCreate,
    HarvestUpdate,
    HarvestWorkFields,
)
from app.farm_operations.models import CropCycle, Harvest, HarvestWork, Plot, QualityEval, WetProcessingInput
from app.farm_operations.models.enums import CycleStatusEnum, HarvestPaymentTypeEnum, HarvestStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.cycle_records import open_harvest
from app.farm_operations.services.dates import format_date
from app.farm_operations.services.mass_balance import check_harvest_total, harvest_processed_kg
from app.farm_operations.services.numbering import last_pass_number, next_pass_number

CENT = Decimal("0.01")
ZERO = Decimal(0)


class HarvestService:
    """
    Cosechas: una sesión por cada pasada de recolección del ciclo.

    Se abre con tarifas por defecto, se registra la recolección de cada
    empleado y se cierra con el total de café cereza (por defecto, la suma de
    los kg registrados). Un ciclo tiene a lo sumo una cosecha abierta.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_harvests(
        self,
        crop_cycle_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        farm_id: Optional[int] = None,
        status: Optional[HarvestStatusEnum] = None,
    ) -> List[dict]:
        query = self.access.cycle_records(Harvest)
        if crop_cycle_id is not None:
            query = query.filter(Harvest.crop_cycle_id == crop_cycle_id)
        if plot_id is not None:
            query = query.filter(CropCycle.plot_id == plot_id)
        if farm_id is not None:
            query = query.filter(Plot.farm_id == farm_id)
        if status is not None:
            query = query.filter(Harvest.status == status)
        harvests = query.order_by(Harvest.start_date.desc(), Harvest.id.desc()).all()
        return self._to_responses(harvests)

    def get_harvest(self, harvest_id: int) -> dict:
        harvest = self.access.get_harvest(harvest_id)
        return {**self._to_responses([harvest])[0], "works": [work_response(w) for w in harvest.works]}

    def get_works(
        self,
        harvest_id: int,
        employee_id: Optional[int] = None,
        paid: Optional[bool] = None,
    ) -> List[dict]:
        harvest = self.access.get_harvest(harvest_id)
        works = [
            work for work in harvest.works
            if (employee_id is None or work.employee_id == employee_id) and (paid is None or work.paid == paid)
        ]
        return [work_response(work) for work in works]

    # ── Cosechas ──────────────────────────────────────────────────────────

    def create_harvest(self, payload: HarvestCreate) -> dict:
        cycle = self.access.get_cycle(payload.crop_cycle_id)
        if cycle.status != CycleStatusEnum.active:
            raise ConflictError("El ciclo está cerrado: no admite cosechas nuevas")
        current = open_harvest(self.db, cycle.id)
        if current is not None:
            raise ConflictError(
                f"Ya hay una cosecha abierta en este ciclo (pasada {current.pass_number}): ciérrala antes de abrir otra"
            )
        if payload.start_date < cycle.start_date:
            raise ConflictError(
                f"La cosecha no puede empezar antes que el ciclo ({format_date(cycle.start_date)})"
            )

        harvest = Harvest(
            crop_cycle_id=cycle.id,
            pass_number=next_pass_number(self.db, cycle.id),
            start_date=payload.start_date,
            rate_per_kg=payload.rate_per_kg,
            rate_per_day=payload.rate_per_day,
            observations=payload.observations,
        )
        self.db.add(harvest)
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            if "uq_harvests_cycle_pass" in str(error.orig):
                raise ConflictError("Otra persona abrió una cosecha en este ciclo al mismo tiempo")
            raise
        return self.get_harvest(harvest.id)

    def update_harvest(self, harvest_id: int, payload: HarvestUpdate) -> dict:
        harvest = self.access.get_harvest(harvest_id)
        is_open = harvest.status == HarvestStatusEnum.open
        closing_fields = (payload.end_date, payload.total_cherry_kg)
        if is_open and any(value is not None for value in closing_fields):
            raise ConflictError("Una cosecha abierta no tiene fecha de fin ni total: ciérrala para fijarlos")
        if not is_open and any(value is None for value in closing_fields):
            raise ConflictError("Una cosecha cerrada necesita su fecha de fin y su total de café cereza")

        self._validate_dates(harvest, payload.start_date, payload.end_date)
        if payload.total_cherry_kg is not None:
            check_harvest_total(self.db, harvest, payload.total_cherry_kg)
        harvest.start_date = payload.start_date
        harvest.rate_per_kg = payload.rate_per_kg
        harvest.rate_per_day = payload.rate_per_day
        harvest.observations = payload.observations
        harvest.end_date = payload.end_date
        harvest.total_cherry_kg = payload.total_cherry_kg
        self.db.commit()
        return self.get_harvest(harvest.id)

    def close_harvest(self, harvest_id: int, payload: HarvestCloseRequest) -> dict:
        """Cierra la sesión con su total de café cereza."""
        harvest = self.access.get_harvest(harvest_id)
        if harvest.status == HarvestStatusEnum.closed:
            raise ConflictError("La cosecha ya está cerrada")
        self._validate_dates(harvest, harvest.start_date, payload.end_date)

        total = payload.total_cherry_kg
        if total is None:
            # Lo registrado en la recolección, o lo ya beneficiado si es más
            registered = sum((work.kg_collected or ZERO for work in harvest.works), ZERO)
            total = max(registered, harvest_processed_kg(self.db, harvest.id))
            if total == 0:
                raise DomainError("Indica el total de café cereza: la recolección no tiene kg registrados")
        check_harvest_total(self.db, harvest, total)

        harvest.status = HarvestStatusEnum.closed
        harvest.end_date = payload.end_date
        harvest.total_cherry_kg = total
        self.db.commit()
        return self.get_harvest(harvest.id)

    def reopen_harvest(self, harvest_id: int) -> dict:
        """Corrige un cierre hecho por error: solo la última pasada de un ciclo activo."""
        harvest = self.access.get_harvest(harvest_id)
        if harvest.status == HarvestStatusEnum.open:
            raise ConflictError("La cosecha ya está abierta")
        if harvest.crop_cycle.status != CycleStatusEnum.active:
            raise ConflictError("El ciclo está cerrado: no se pueden reabrir sus cosechas")
        if harvest.pass_number != last_pass_number(self.db, harvest.crop_cycle_id):
            raise ConflictError("Solo se puede reabrir la última pasada del ciclo")

        harvest.status = HarvestStatusEnum.open
        harvest.end_date = None
        harvest.total_cherry_kg = None
        self.db.commit()
        return self.get_harvest(harvest.id)

    def delete_harvest(self, harvest_id: int) -> None:
        """Elimina una cosecha abierta por error: sin recolección registrada."""
        harvest = self.access.get_harvest(harvest_id)
        if harvest.works:
            raise ConflictError("No se puede eliminar: la cosecha tiene recolección registrada")
        if harvest_processed_kg(self.db, harvest.id) > 0:
            raise ConflictError("No se puede eliminar: su café ya está en un beneficio")
        if self.db.query(QualityEval.id).filter(QualityEval.harvest_id == harvest.id).first():
            raise ConflictError("No se puede eliminar: la cosecha tiene evaluaciones de calidad")
        self.db.delete(harvest)
        self.db.commit()

    # ── Recolección ───────────────────────────────────────────────────────

    def create_work(self, harvest_id: int, payload: HarvestWorkFields) -> dict:
        harvest = self.access.get_harvest(harvest_id)
        work = HarvestWork(harvest_id=harvest.id)
        self._fill_work(work, harvest, payload)
        self.db.add(work)
        self.db.commit()
        self.db.refresh(work)
        return work_response(work)

    def update_work(self, work_id: int, payload: HarvestWorkFields) -> dict:
        work = self.access.get_harvest_work(work_id)
        if work.paid:
            raise ConflictError("Un trabajo pagado no se modifica: deshaz el pago primero")
        self._fill_work(work, work.harvest, payload)
        self.db.commit()
        self.db.refresh(work)
        return work_response(work)

    def delete_work(self, work_id: int) -> None:
        work = self.access.get_harvest_work(work_id)
        if work.paid:
            raise ConflictError("Un trabajo pagado no se elimina: deshaz el pago primero")
        self._require_open(work.harvest)
        self.db.delete(work)
        self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    @staticmethod
    def _require_open(harvest: Harvest) -> None:
        if harvest.status != HarvestStatusEnum.open:
            raise ConflictError("La cosecha está cerrada: reábrela para corregir su recolección")

    def _fill_work(self, work: HarvestWork, harvest: Harvest, payload: HarvestWorkFields) -> None:
        """Valida la recolección y calcula su valor con las tarifas de la cosecha."""
        self._require_open(harvest)
        employee = self.access.get_employee(payload.employee_id)
        if employee.farm_id != harvest.crop_cycle.plot.farm_id:
            raise ConflictError("El empleado no es de esta finca")
        if not employee.active and employee.id != work.employee_id:
            raise ConflictError(f"{employee.full_name} está inactivo: actívalo para registrarle recolección")
        if payload.work_date < harvest.start_date:
            raise ConflictError(
                f"La fecha es anterior al inicio de la cosecha ({format_date(harvest.start_date)})"
            )

        if payload.payment_type == HarvestPaymentTypeEnum.per_kg:
            rate = payload.rate_per_kg or harvest.rate_per_kg
            if rate is None:
                raise DomainError("Indica la tarifa por kg: la cosecha no tiene una por defecto")
            work.rate_per_kg, work.day_value = rate, None
            work.total_value = (payload.kg_collected * rate).quantize(CENT, rounding=ROUND_HALF_UP)
        else:
            value = payload.day_value or harvest.rate_per_day
            if value is None:
                raise DomainError("Indica el valor del jornal: la cosecha no tiene uno por defecto")
            work.rate_per_kg, work.day_value = None, value
            work.total_value = value

        work.employee_id = employee.id
        work.work_date = payload.work_date
        work.payment_type = payload.payment_type
        work.kg_collected = payload.kg_collected

    def _validate_dates(self, harvest: Harvest, start: date, end: Optional[date]) -> None:
        """La cosecha cabe en su ciclo y cubre su recolección."""
        cycle = harvest.crop_cycle
        if start < cycle.start_date:
            raise ConflictError(f"La cosecha no puede empezar antes que el ciclo ({format_date(cycle.start_date)})")
        if end is not None and end < start:
            raise ConflictError(f"La fecha de fin no puede ser anterior al inicio ({format_date(start)})")
        if end is not None and cycle.end_date is not None and end > cycle.end_date:
            raise ConflictError(f"La cosecha no puede terminar después del cierre del ciclo ({format_date(cycle.end_date)})")

        dates = [work.work_date for work in harvest.works]
        if dates and start > min(dates):
            raise ConflictError(f"Hay recolección desde el {format_date(min(dates))}: la cosecha no puede empezar después")
        if dates and end is not None and end < max(dates):
            raise ConflictError(f"Hay recolección hasta el {format_date(max(dates))}: la cosecha no puede terminar antes")

    def _to_responses(self, harvests: List[Harvest]) -> List[dict]:
        if not harvests:
            return []
        totals = {
            row.harvest_id: row
            for row in self.db.query(
                HarvestWork.harvest_id,
                func.count(HarvestWork.id).label("works_count"),
                func.coalesce(func.sum(HarvestWork.kg_collected), 0).label("kg_registered"),
                func.coalesce(func.sum(HarvestWork.total_value), 0).label("value_total"),
                func.coalesce(
                    func.sum(case((HarvestWork.paid.is_(False), HarvestWork.total_value), else_=0)), 0
                ).label("value_pending"),
            )
            .filter(HarvestWork.harvest_id.in_([harvest.id for harvest in harvests]))
            .group_by(HarvestWork.harvest_id)
            .all()
        }

        processed = dict(
            self.db.query(WetProcessingInput.harvest_id, func.sum(WetProcessingInput.cherry_kg))
            .filter(WetProcessingInput.harvest_id.in_([harvest.id for harvest in harvests]))
            .group_by(WetProcessingInput.harvest_id)
            .all()
        )

        responses = []
        for harvest in harvests:
            cycle = harvest.crop_cycle
            row = totals.get(harvest.id)
            responses.append({
                "id": harvest.id,
                "crop_cycle_id": cycle.id,
                "cycle_number": cycle.cycle_number,
                "plot_id": cycle.plot_id,
                "plot_name": cycle.plot.name,
                "farm_id": cycle.plot.farm_id,
                "pass_number": harvest.pass_number,
                "start_date": harvest.start_date,
                "end_date": harvest.end_date,
                "status": harvest.status,
                "rate_per_kg": harvest.rate_per_kg,
                "rate_per_day": harvest.rate_per_day,
                "total_cherry_kg": harvest.total_cherry_kg,
                "observations": harvest.observations,
                "created_at": harvest.created_at,
                "works_count": row.works_count if row else 0,
                "kg_registered": row.kg_registered if row else ZERO,
                "value_total": row.value_total if row else ZERO,
                "value_pending": row.value_pending if row else ZERO,
                "kg_processed": processed.get(harvest.id, ZERO),
            })
        return responses


def work_response(work: HarvestWork) -> dict:
    return {
        "id": work.id,
        "harvest_id": work.harvest_id,
        "employee_id": work.employee_id,
        "employee_name": work.employee.full_name,
        "work_date": work.work_date,
        "payment_type": work.payment_type,
        "kg_collected": work.kg_collected,
        "rate_per_kg": work.rate_per_kg,
        "day_value": work.day_value,
        "total_value": work.total_value,
        "paid": work.paid,
        "paid_at": work.paid_at,
        "created_at": work.created_at,
    }
