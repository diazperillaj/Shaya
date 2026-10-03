from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.api.v1.crop_cycles.schema import CycleCloseRequest, CycleCreate, CycleUpdate
from app.farm_operations.models import CropCycle, Plot
from app.farm_operations.models.enums import CycleStatusEnum, PlotStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.cycle_records import open_harvest, record_date_bounds, records_summary
from app.farm_operations.services.dates import format_date
from app.farm_operations.services.numbering import last_cycle, next_cycle_number


class CropCycleService:
    """
    Ciclos productivos de los lotes.

    Un lote tiene a lo sumo un ciclo activo y sus ciclos no se solapan: cada
    uno empieza cuando terminó el anterior o después. El rango de fechas de
    un ciclo siempre cubre sus labores y sus cosechas, y se cierra cuando ya
    no tiene cosechas abiertas.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_cycles(
        self,
        plot_id: Optional[int] = None,
        farm_id: Optional[int] = None,
        status: Optional[CycleStatusEnum] = None,
    ) -> List[dict]:
        query = self.access.cycles()
        if plot_id is not None:
            query = query.filter(CropCycle.plot_id == plot_id)
        if farm_id is not None:
            query = query.filter(Plot.farm_id == farm_id)
        if status is not None:
            query = query.filter(CropCycle.status == status)
        cycles = query.order_by(Plot.name, CropCycle.cycle_number.desc()).all()
        return [self._to_response(cycle) for cycle in cycles]

    def get_cycle(self, cycle_id: int) -> dict:
        cycle = self.access.get_cycle(cycle_id)
        return {**self._to_response(cycle), "summary": records_summary(self.db, cycle.id)}

    # ── Escritura ─────────────────────────────────────────────────────────

    def create_cycle(self, payload: CycleCreate) -> dict:
        plot = self.access.get_plot(payload.plot_id)
        if plot.status == PlotStatusEnum.closed:
            raise ConflictError("El lote está cerrado: no admite ciclos nuevos")

        active = self._active_cycle(plot.id)
        if active is not None:
            raise ConflictError(f"El lote ya tiene un ciclo activo (ciclo {active.cycle_number})")

        last = last_cycle(self.db, plot.id)
        self._validate_start(plot, payload.start_date, previous=last)

        cycle = CropCycle(
            plot_id=plot.id,
            cycle_number=next_cycle_number(self.db, plot.id),
            start_date=payload.start_date,
            observations=payload.observations,
        )
        self.db.add(cycle)
        try:
            self.db.commit()
        except IntegrityError as error:
            # Dos aperturas simultáneas: el índice parcial deja pasar solo una
            self.db.rollback()
            if "uq_crop_cycles" in str(error.orig):
                raise ConflictError("El lote ya tiene un ciclo activo")
            raise
        return self.get_cycle(cycle.id)

    def update_cycle(self, cycle_id: int, payload: CycleUpdate) -> dict:
        cycle = self.access.get_cycle(cycle_id)
        is_active = cycle.status == CycleStatusEnum.active
        if is_active and payload.end_date is not None:
            raise ConflictError("Un ciclo activo no tiene fecha de fin: ciérralo para fijarla")
        if not is_active and payload.end_date is None:
            raise ConflictError("Un ciclo cerrado necesita su fecha de fin")

        self._validate_range(cycle, payload.start_date, payload.end_date)
        cycle.start_date = payload.start_date
        cycle.end_date = payload.end_date
        cycle.observations = payload.observations
        self.db.commit()
        return self.get_cycle(cycle.id)

    def close_cycle(self, cycle_id: int, payload: CycleCloseRequest) -> dict:
        """Cierra el ciclo al terminar su cosecha."""
        cycle = self.access.get_cycle(cycle_id)
        if cycle.status == CycleStatusEnum.closed:
            raise ConflictError("El ciclo ya está cerrado")
        harvest = open_harvest(self.db, cycle.id)
        if harvest is not None:
            raise ConflictError(f"Cierra primero la cosecha abierta (pasada {harvest.pass_number})")
        self._validate_range(cycle, cycle.start_date, payload.end_date)

        cycle.status = CycleStatusEnum.closed
        cycle.end_date = payload.end_date
        self.db.commit()
        return self.get_cycle(cycle.id)

    def reopen_cycle(self, cycle_id: int) -> dict:
        """Corrige un cierre hecho por error: solo el último ciclo de un lote activo."""
        cycle = self.access.get_cycle(cycle_id)
        if cycle.status == CycleStatusEnum.active:
            raise ConflictError("El ciclo ya está activo")
        if cycle.plot.status == PlotStatusEnum.closed:
            raise ConflictError("El lote está cerrado: no se pueden reabrir sus ciclos")
        if last_cycle(self.db, cycle.plot_id).id != cycle.id:
            raise ConflictError("Solo se puede reabrir el último ciclo del lote")

        cycle.status = CycleStatusEnum.active
        cycle.end_date = None
        self.db.commit()
        return self.get_cycle(cycle.id)

    def delete_cycle(self, cycle_id: int) -> None:
        """Elimina un ciclo abierto por error: sin labores registradas."""
        cycle = self.access.get_cycle(cycle_id)
        first, _ = record_date_bounds(self.db, cycle.id)
        if first is not None:
            raise ConflictError("No se puede eliminar: el ciclo tiene labores o cosechas registradas")
        self.db.delete(cycle)
        self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    def _active_cycle(self, plot_id: int) -> Optional[CropCycle]:
        return (
            self.db.query(CropCycle)
            .filter(CropCycle.plot_id == plot_id, CropCycle.status == CycleStatusEnum.active)
            .first()
        )

    def _neighbor(self, cycle: CropCycle, before: bool) -> Optional[CropCycle]:
        """Ciclo anterior o siguiente del mismo lote."""
        query = self.db.query(CropCycle).filter(CropCycle.plot_id == cycle.plot_id)
        if before:
            query = query.filter(CropCycle.cycle_number < cycle.cycle_number)
            return query.order_by(CropCycle.cycle_number.desc()).first()
        query = query.filter(CropCycle.cycle_number > cycle.cycle_number)
        return query.order_by(CropCycle.cycle_number).first()

    @staticmethod
    def _validate_start(plot: Plot, start: date, previous: Optional[CropCycle]) -> None:
        if plot.planting_date and start < plot.planting_date:
            raise ConflictError(
                f"El ciclo no puede empezar antes de la siembra ({format_date(plot.planting_date)})"
            )
        if previous is not None and previous.end_date and start < previous.end_date:
            raise ConflictError(
                f"El ciclo no puede empezar antes de que termine el ciclo {previous.cycle_number} "
                f"({format_date(previous.end_date)})"
            )

    def _validate_range(self, cycle: CropCycle, start: date, end: Optional[date]) -> None:
        """Las fechas no solapan los ciclos vecinos y cubren todas las labores del ciclo."""
        if end is not None and end < start:
            raise ConflictError(f"La fecha de fin no puede ser anterior al inicio ({format_date(start)})")

        self._validate_start(cycle.plot, start, previous=self._neighbor(cycle, before=True))
        following = self._neighbor(cycle, before=False)
        if following is not None and end is not None and end > following.start_date:
            raise ConflictError(
                f"El ciclo no puede terminar después de que empezó el ciclo {following.cycle_number} "
                f"({format_date(following.start_date)})"
            )

        first, last = record_date_bounds(self.db, cycle.id)
        if first is not None and start > first:
            raise ConflictError(
                f"Hay labores o cosechas desde el {format_date(first)}: el ciclo no puede empezar después"
            )
        if last is not None and end is not None and end < last:
            raise ConflictError(
                f"Hay labores o cosechas hasta el {format_date(last)}: el ciclo no puede terminar antes"
            )

    @staticmethod
    def _to_response(cycle: CropCycle) -> dict:
        return {
            "id": cycle.id,
            "plot_id": cycle.plot_id,
            "plot_name": cycle.plot.name,
            "farm_id": cycle.plot.farm_id,
            "cycle_number": cycle.cycle_number,
            "start_date": cycle.start_date,
            "end_date": cycle.end_date,
            "status": cycle.status,
            "observations": cycle.observations,
            "created_at": cycle.created_at,
        }


def active_cycles_by_plot(db: Session, plot_ids: List[int]) -> dict[int, CropCycle]:
    """Ciclo activo de cada lote (los lotes sin ciclo activo no aparecen)."""
    if not plot_ids:
        return {}
    cycles = (
        db.query(CropCycle)
        .filter(CropCycle.plot_id.in_(plot_ids), CropCycle.status == CycleStatusEnum.active)
        .all()
    )
    return {cycle.plot_id: cycle for cycle in cycles}


def last_cycle_end(db: Session, plot_id: int) -> Optional[date]:
    """Fecha de fin del último ciclo cerrado del lote."""
    return db.query(func.max(CropCycle.end_date)).filter(CropCycle.plot_id == plot_id).scalar()
