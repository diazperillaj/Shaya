from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.api.v1.crop_cycles.service import active_cycles_by_plot, last_cycle_end
from app.farm_operations.api.v1.plots.schema import (
    PlotCloseRequest,
    PlotCreate,
    PlotEventCreate,
    PlotReopenRequest,
    PlotUpdate,
)
from app.farm_operations.api.v1.validation import clean_other_detail
from app.farm_operations.models import ClimateRecord, CropCycle, DayLabor, Plot, PlotEvent, SoilAnalysis
from app.farm_operations.models.enums import PlotEventTypeEnum, PlotStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.dates import business_date, business_today, format_date

DAYS_PER_YEAR = Decimal("365.25")

# Campos del formulario de lote (terreno, siembra y procedencia de la semilla)
PLOT_FIELDS = (
    "area", "slope", "soil_type", "location",
    "variety", "planting_date", "initial_age_years", "seedling_count",
    "row_spacing_m", "plant_spacing_m", "shade_type",
    "seed_supplier", "seed_origin_place", "seed_purchase_date", "seed_cost",
    "observations",
)


def effective_age_years(plot: Plot, last_zoca: Optional[date], today: date) -> Decimal:
    """
    Edad efectiva del cultivo, en años con un decimal.

    Se cuenta desde la última zoca, o desde la siembra; si el lote se
    registró ya establecido, desde la edad indicada al registrarlo. Al
    cerrarse el lote, la edad queda congelada en la fecha de cierre.
    """
    until = plot.closed_at or today
    if last_zoca:
        start, base = last_zoca, Decimal(0)
    elif plot.planting_date:
        start, base = plot.planting_date, Decimal(0)
    else:
        start, base = business_date(plot.created_at), plot.initial_age_years

    elapsed = Decimal(max((until - start).days, 0)) / DAYS_PER_YEAR
    return (base + elapsed).quantize(Decimal("0.1"))


class PlotService:
    """Lotes del módulo de cultivo, siempre dentro del alcance del usuario."""

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_plots(
        self,
        farm_id: Optional[int] = None,
        status: Optional[PlotStatusEnum] = None,
        variety: Optional[str] = None,
    ) -> List[dict]:
        query = self.access.plots()
        if farm_id is not None:
            query = query.filter(Plot.farm_id == farm_id)
        if status is not None:
            query = query.filter(Plot.status == status)
        if variety:
            query = query.filter(Plot.variety.ilike(f"%{variety.strip()}%"))

        plots = query.order_by(Plot.status, Plot.name).all()
        return self._to_responses(plots)

    def get_plot(self, plot_id: int) -> dict:
        return self._to_responses([self.access.get_plot(plot_id)])[0]

    def get_renewal_defaults(self, plot_id: int) -> dict:
        plot = self.access.get_plot(plot_id)
        return {
            "farm_id": plot.farm_id,
            "renewed_from_plot_id": plot.id,
            "name": plot.name,
            "area": plot.area,
            "slope": plot.slope,
            "soil_type": plot.soil_type,
            "location": plot.location,
        }

    def get_events(self, plot_id: int) -> List[PlotEvent]:
        return self.access.get_plot(plot_id).events

    # ── Escritura ─────────────────────────────────────────────────────────

    def create_plot(self, payload: PlotCreate) -> dict:
        farm = self.access.get_farm(payload.farm_id)
        if payload.renewed_from_plot_id is not None:
            self._validate_renewal(farm.id, payload.renewed_from_plot_id)
        self._validate_unique_active_name(farm.id, payload.name)

        plot = Plot(
            farm_id=farm.id,
            name=payload.name.strip(),
            renewed_from_plot_id=payload.renewed_from_plot_id,
            **{field: getattr(payload, field) for field in PLOT_FIELDS},
        )
        self.db.add(plot)
        self._commit_unique_name(plot.name)
        return self.get_plot(plot.id)

    def update_plot(self, plot_id: int, payload: PlotUpdate) -> dict:
        plot = self.access.get_plot(plot_id)
        if plot.status == PlotStatusEnum.active:
            self._validate_unique_active_name(plot.farm_id, payload.name, exclude_id=plot.id)

        plot.name = payload.name.strip()
        for field in PLOT_FIELDS:
            setattr(plot, field, getattr(payload, field))
        self._commit_unique_name(plot.name)
        return self.get_plot(plot.id)

    def close_plot(self, plot_id: int, payload: PlotCloseRequest) -> dict:
        """Cierre definitivo: el lote dejó de dar cosecha."""
        plot = self.access.get_plot(plot_id)
        if plot.status == PlotStatusEnum.closed:
            raise ConflictError("El lote ya está cerrado")
        if plot.planting_date and payload.closed_at < plot.planting_date:
            raise ConflictError("La fecha de cierre no puede ser anterior a la siembra")

        active = active_cycles_by_plot(self.db, [plot.id]).get(plot.id)
        if active is not None:
            raise ConflictError(f"Cierra primero el ciclo activo del lote (ciclo {active.cycle_number})")
        last_end = last_cycle_end(self.db, plot.id)
        if last_end is not None and payload.closed_at < last_end:
            raise ConflictError(
                f"La fecha de cierre no puede ser anterior al fin del último ciclo ({format_date(last_end)})"
            )

        plot.status = PlotStatusEnum.closed
        plot.closed_at = payload.closed_at
        self.db.add(PlotEvent(
            plot_id=plot.id,
            event_type=PlotEventTypeEnum.closure,
            event_date=payload.closed_at,
            description=payload.description,
        ))
        self.db.commit()
        return self.get_plot(plot.id)

    def reopen_plot(self, plot_id: int, payload: PlotReopenRequest) -> dict:
        """Corrige un cierre hecho por error; un lote ya renovado no se reabre."""
        plot = self.access.get_plot(plot_id)
        if plot.status == PlotStatusEnum.active:
            raise ConflictError("El lote ya está activo")

        renewal = self._renewal_of(plot.id)
        if renewal is not None:
            raise ConflictError(
                f"No se puede reabrir: el terreno ya se volvió a sembrar en el lote «{renewal.name}»"
            )

        plot.status = PlotStatusEnum.active
        plot.closed_at = None
        self.db.add(PlotEvent(
            plot_id=plot.id,
            event_type=PlotEventTypeEnum.reopening,
            event_date=business_today(),
            description=payload.description,
        ))
        self._commit_unique_name(plot.name)
        return self.get_plot(plot.id)

    def delete_plot(self, plot_id: int) -> None:
        """Elimina un lote recién creado: sin historial, ciclos, registros ni renovaciones."""
        plot = self.access.get_plot(plot_id)
        if self.db.query(PlotEvent.id).filter(PlotEvent.plot_id == plot.id).first():
            raise ConflictError("No se puede eliminar: el lote tiene historial de eventos")
        if self.db.query(CropCycle.id).filter(CropCycle.plot_id == plot.id).first():
            raise ConflictError("No se puede eliminar: el lote tiene ciclos productivos")
        if any(
            self.db.query(model.id).filter(model.plot_id == plot.id).first()
            for model in (SoilAnalysis, ClimateRecord, DayLabor)
        ):
            raise ConflictError("No se puede eliminar: el lote tiene análisis de suelo, clima o jornales registrados")
        if self._renewal_of(plot.id) is not None:
            raise ConflictError("No se puede eliminar: otro lote es su renovación")

        self.db.delete(plot)
        self.db.commit()

    def create_event(self, plot_id: int, payload: PlotEventCreate) -> PlotEvent:
        plot = self.access.get_plot(plot_id)
        if plot.status == PlotStatusEnum.closed:
            raise ConflictError("El lote está cerrado: no admite eventos nuevos")

        event = PlotEvent(
            plot_id=plot.id,
            event_type=payload.event_type,
            event_date=payload.event_date,
            other_detail=clean_other_detail(payload.event_type == PlotEventTypeEnum.other, payload.other_detail),
            description=payload.description,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    # ── Internos ──────────────────────────────────────────────────────────

    def _validate_renewal(self, farm_id: int, previous_id: int) -> None:
        previous = self.access.get_plot(previous_id)
        if previous.farm_id != farm_id:
            raise ConflictError("El lote que se renueva debe ser de la misma finca")
        if previous.status != PlotStatusEnum.closed:
            raise ConflictError("Solo se puede renovar un lote cerrado")
        if self._renewal_of(previous.id) is not None:
            raise ConflictError("Ese lote ya fue renovado")

    def _validate_unique_active_name(self, farm_id: int, name: str, exclude_id: Optional[int] = None) -> None:
        query = self.db.query(Plot.id).filter(
            Plot.farm_id == farm_id,
            Plot.status == PlotStatusEnum.active,
            Plot.name.ilike(name.strip()),
        )
        if exclude_id is not None:
            query = query.filter(Plot.id != exclude_id)
        if query.first():
            raise ConflictError(f"Ya hay un lote activo llamado «{name.strip()}» en esta finca")

    def _commit_unique_name(self, name: str) -> None:
        """Confirma, traduciendo el choque con el índice de nombre único entre lotes activos."""
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            if "uq_plots_farm_name_active" in str(error.orig):
                raise ConflictError(f"Ya hay un lote activo llamado «{name}» en esta finca")
            raise

    def _renewal_of(self, plot_id: int) -> Optional[Plot]:
        return self.db.query(Plot).filter(Plot.renewed_from_plot_id == plot_id).first()

    def _to_responses(self, plots: List[Plot]) -> List[dict]:
        if not plots:
            return []
        ids = [plot.id for plot in plots]

        last_zocas = dict(
            self.db.query(PlotEvent.plot_id, func.max(PlotEvent.event_date))
            .filter(PlotEvent.plot_id.in_(ids), PlotEvent.event_type == PlotEventTypeEnum.zoca)
            .group_by(PlotEvent.plot_id)
            .all()
        )
        renewals = dict(
            self.db.query(Plot.renewed_from_plot_id, Plot.id)
            .filter(Plot.renewed_from_plot_id.in_(ids))
            .all()
        )
        active_cycles = active_cycles_by_plot(self.db, ids)

        today = business_today()
        responses = []
        for plot in plots:
            last_zoca = last_zocas.get(plot.id)
            active_cycle = active_cycles.get(plot.id)
            responses.append({
                "id": plot.id,
                "farm_id": plot.farm_id,
                "farm_name": plot.farm.name,
                "name": plot.name,
                "status": plot.status,
                "renewed_from_plot_id": plot.renewed_from_plot_id,
                "renewed_by_plot_id": renewals.get(plot.id),
                **{field: getattr(plot, field) for field in PLOT_FIELDS},
                "closed_at": plot.closed_at,
                "created_at": plot.created_at,
                "effective_age_years": effective_age_years(plot, last_zoca, today),
                "last_zoca_date": last_zoca,
                "active_cycle": {
                    "id": active_cycle.id,
                    "cycle_number": active_cycle.cycle_number,
                    "start_date": active_cycle.start_date,
                } if active_cycle else None,
            })
        return responses
