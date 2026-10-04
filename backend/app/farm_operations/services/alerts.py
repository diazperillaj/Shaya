"""
Alertas y recordatorios del módulo de cultivo (dashboards-alertas §4 y §6).

Se calculan al consultar y no se guardan (API A4): una función por tipo de
alerta, registrada en `CHECKS`, que hace una consulta agregada sobre todas
las fincas del alcance. Agregar una alerta = agregar una función.

Las alertas solo informan, nunca bloquean (arquitectura §7.2). Los umbrales
se resuelven lote → finca → valor por defecto; las de beneficio y secado,
que no tienen un lote único (mezclas), a nivel de finca.
"""

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Callable, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.farm_operations.models import (
    AlertConfig,
    ClimateRecord,
    CropCycle,
    CulturalPractice,
    DayLabor,
    Drying,
    Employee,
    Farm,
    Fertilization,
    FloweringRecord,
    Harvest,
    HarvestWork,
    Irrigation,
    PestMonitoring,
    PhytosanitaryApp,
    Plot,
    QualityEval,
    WetProcessing,
)
from app.farm_operations.models.enums import (
    CulturalPracticeTypeEnum,
    CycleStatusEnum,
    DryingStatusEnum,
    HarvestStatusEnum,
    IntensityEnum,
    PlotStatusEnum,
    QualityStageEnum,
    WetProcessingStatusEnum,
)
from app.farm_operations.services.cycle_records import CYCLE_LABORS
from app.farm_operations.services.dates import BUSINESS_TZ, business_today, format_date
from app.farm_operations.services.traceability import traced_cherry_select

# Valores iniciales de práctica cafetera colombiana (dashboards-alertas §4).
# Son puntos de partida, no verdades agronómicas: cada finca o lote los
# ajusta. None = recordatorio desactivado (el riego, porque la mayoría del
# café es de secano).
DEFAULTS: dict[str, Optional[Decimal]] = {
    "fertilization_reminder_days": Decimal(120),
    "irrigation_reminder_days": None,
    "phytosanitary_reminder_days": Decimal(30),
    "weeding_reminder_days": Decimal(75),
    "harvest_reminder_days": Decimal(15),
    "inactivity_alert_days": Decimal(45),
    "max_drying_days": Decimal(15),
    "min_final_humidity": Decimal(10),
    "max_final_humidity": Decimal(12),
    "min_fermentation_hours": Decimal(10),
    "max_fermentation_hours": Decimal(24),
    "broca_alert_pct": Decimal(2),
}

PARAMETERS = tuple(DEFAULTS)

# Umbrales fijos de §4 (sin parámetro configurable)
RECENT_DAYS = 30            # las alertas sobre hechos ya cerrados miran solo el último mes
QUALITY_GRACE_DAYS = 7      # margen para evaluar el pergamino de un secado
UNPAID_DAYS = 15
HARVEST_OPEN_DAYS = 30
YIELD_DROP_POINTS = Decimal(3)
HISTORY_DAYS = 365          # histórico de rendimiento de la finca
MIN_HISTORY_DRYINGS = 3
FLOWERING_TO_HARVEST_DAYS = 224   # ≈ 32 semanas (§5)
HARVEST_ESTIMATE_RANGE_DAYS = 14

SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


def resolve(*levels: tuple[str, Optional[AlertConfig]]) -> dict[str, dict]:
    """
    Valor efectivo de cada parámetro y el nivel del que sale.

    Recibe los niveles de mayor a menor prioridad, p. ej.
    `resolve(("plot", config_lote), ("farm", config_finca))`. Un valor NULL
    hereda del nivel siguiente; si ninguno lo define, aplica el default.

    Returns:
        `{parámetro: {"value": ..., "source": "plot" | "farm" | "default"}}`
    """
    resolved = {}
    for name in PARAMETERS:
        for source, config in levels:
            value = getattr(config, name) if config is not None else None
            if value is not None:
                resolved[name] = {"value": value, "source": source}
                break
        else:
            resolved[name] = {"value": DEFAULTS[name], "source": "default"}
    return resolved


# ═══════════════════════════════════════════════════════════════════════════
# Alerta y contexto de cálculo
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Alert:
    type: str
    severity: str                       # info | medium | high
    farm_id: int
    farm_name: str
    plot_id: Optional[int]
    plot_name: Optional[str]
    entity: dict                        # a qué enlaza: lote, cosecha, beneficio, secado o pagos
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    since: Optional[date] = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class CycleRow:
    cycle_id: int
    number: int
    start: date
    plot_id: int
    plot_name: str
    farm_id: int


@dataclass
class Context:
    db: Session
    farm_ids: list[int]
    today: date
    now: datetime
    farm_names: dict[int, str]
    farm_configs: dict[int, AlertConfig]
    plot_configs: dict[int, AlertConfig]
    _cycles: Optional[list] = field(default=None, repr=False)

    def plot_value(self, plot_id: int, farm_id: int, name: str) -> Optional[Decimal]:
        return resolve(("plot", self.plot_configs.get(plot_id)), ("farm", self.farm_configs.get(farm_id)))[name]["value"]

    def farm_value(self, farm_id: int, name: str) -> Optional[Decimal]:
        return resolve(("farm", self.farm_configs.get(farm_id)))[name]["value"]

    def active_cycles(self) -> list[CycleRow]:
        """Ciclos activos de lotes activos: a ellos se refieren los recordatorios."""
        if self._cycles is None:
            rows = (
                self.db.query(CropCycle.id, CropCycle.cycle_number, CropCycle.start_date, Plot.id, Plot.name, Plot.farm_id)
                .join(Plot, CropCycle.plot_id == Plot.id)
                .filter(
                    Plot.farm_id.in_(self.farm_ids),
                    Plot.status == PlotStatusEnum.active,
                    CropCycle.status == CycleStatusEnum.active,
                )
                .order_by(Plot.farm_id, Plot.name)
                .all()
            )
            self._cycles = [CycleRow(*row) for row in rows]
        return self._cycles

    def alert(self, type_: str, severity: str, farm_id: int, entity: dict, message: str,
              plot_id: Optional[int] = None, plot_name: Optional[str] = None,
              value=None, threshold=None, since: Optional[date] = None) -> Alert:
        return Alert(
            type=type_, severity=severity, farm_id=farm_id, farm_name=self.farm_names.get(farm_id, ""),
            plot_id=plot_id, plot_name=plot_name, entity=entity, message=message,
            value=float(value) if value is not None else None,
            threshold=float(threshold) if threshold is not None else None,
            since=since,
        )


def _number(value) -> str:
    """Número para mensajes: 12,5 o 12."""
    text = format(Decimal(str(value)).quantize(Decimal("0.1")).normalize(), "f")
    return text.replace(".", ",")


def money(value) -> str:
    return "$ " + f"{Decimal(value):,.0f}".replace(",", ".")


def _max_dates(ctx: Context, model, column, extra=None) -> dict[int, date]:
    """Última fecha por ciclo de un tipo de registro."""
    ids = [c.cycle_id for c in ctx.active_cycles()]
    if not ids:
        return {}
    query = ctx.db.query(model.crop_cycle_id, func.max(column)).filter(model.crop_cycle_id.in_(ids))
    if extra is not None:
        query = query.filter(extra)
    return dict(query.group_by(model.crop_cycle_id).all())


# ═══════════════════════════════════════════════════════════════════════════
# Recordatorios de labores (info, §4.1)
# ═══════════════════════════════════════════════════════════════════════════


def _labor_reminders(ctx: Context, type_: str, parameter: str, phrase: str, last: dict[int, date]) -> list[Alert]:
    alerts = []
    for cycle in ctx.active_cycles():
        threshold = ctx.plot_value(cycle.plot_id, cycle.farm_id, parameter)
        if threshold is None:
            continue
        since = last.get(cycle.cycle_id) or cycle.start
        days = (ctx.today - since).days
        if days > threshold:
            what = phrase if cycle.cycle_id in last else f"{phrase} en el ciclo"
            alerts.append(ctx.alert(
                type_, "info", cycle.farm_id, {"plot_id": cycle.plot_id, "crop_cycle_id": cycle.cycle_id},
                f"Lote «{cycle.plot_name}» · ciclo {cycle.number}: {days} días {what} (recordatorio cada {threshold})",
                cycle.plot_id, cycle.plot_name, days, threshold, since,
            ))
    return alerts


def fertilization_due(ctx: Context) -> list[Alert]:
    last = _max_dates(ctx, Fertilization, Fertilization.application_date)
    return _labor_reminders(ctx, "fertilization_due", "fertilization_reminder_days", "sin fertilizar", last)


def phytosanitary_due(ctx: Context) -> list[Alert]:
    """El recordatorio empuja a muestrear (MIB): cuenta el último muestreo o control de plagas."""
    monitored = _max_dates(ctx, PestMonitoring, PestMonitoring.monitoring_date)
    applied = _max_dates(ctx, PhytosanitaryApp, PhytosanitaryApp.application_date)
    last = {cid: max(d for d in (monitored.get(cid), applied.get(cid)) if d is not None)
            for cid in set(monitored) | set(applied)}
    return _labor_reminders(ctx, "phytosanitary_due", "phytosanitary_reminder_days",
                            "sin muestreo ni control de plagas", last)


def weeding_due(ctx: Context) -> list[Alert]:
    last = _max_dates(ctx, CulturalPractice, CulturalPractice.practice_date,
                      CulturalPractice.practice_type == CulturalPracticeTypeEnum.weeding)
    return _labor_reminders(ctx, "weeding_due", "weeding_reminder_days", "sin deshierba", last)


def irrigation_due(ctx: Context) -> list[Alert]:
    last = _max_dates(ctx, Irrigation, Irrigation.irrigation_date)
    return _labor_reminders(ctx, "irrigation_due", "irrigation_reminder_days", "sin riego", last)


def main_flowering(ctx: Context, cycle_ids: list[int]) -> dict[int, date]:
    """Floración principal de cada ciclo: la de mayor intensidad y, entre iguales, la primera (§5)."""
    if not cycle_ids:
        return {}
    rank = {IntensityEnum.high: 0, IntensityEnum.medium: 1, IntensityEnum.low: 2}
    rows = (
        ctx.db.query(FloweringRecord.crop_cycle_id, FloweringRecord.flowering_date, FloweringRecord.intensity)
        .filter(FloweringRecord.crop_cycle_id.in_(cycle_ids)).all()
    )
    best: dict[int, tuple] = {}
    for cycle_id, day, intensity in rows:
        key = (rank[intensity], day)
        if cycle_id not in best or key < best[cycle_id]:
            best[cycle_id] = key
    return {cycle_id: key[1] for cycle_id, key in best.items()}


def estimated_harvest(flowering: Optional[date]) -> Optional[date]:
    return flowering + timedelta(days=FLOWERING_TO_HARVEST_DAYS) if flowering else None


def harvest_pass_due(ctx: Context) -> list[Alert]:
    """
    La siguiente pasada: hace más de N días cerró la última y no hay otra
    abierta; o, sin cosechas en el ciclo, ya pasó la fecha estimada por la
    floración.
    """
    cycles = ctx.active_cycles()
    ids = [c.cycle_id for c in cycles]
    if not ids:
        return []
    harvests: dict[int, list] = {}
    for cycle_id, number, status, end in (
        ctx.db.query(Harvest.crop_cycle_id, Harvest.pass_number, Harvest.status, Harvest.end_date)
        .filter(Harvest.crop_cycle_id.in_(ids)).all()
    ):
        harvests.setdefault(cycle_id, []).append((number, status, end))
    flowering = main_flowering(ctx, ids)
    alerts = []
    for cycle in cycles:
        threshold = ctx.plot_value(cycle.plot_id, cycle.farm_id, "harvest_reminder_days")
        if threshold is None:
            continue
        passes = harvests.get(cycle.cycle_id, [])
        entity = {"plot_id": cycle.plot_id, "crop_cycle_id": cycle.cycle_id}
        if any(status == HarvestStatusEnum.open for _, status, _ in passes):
            continue
        if passes:
            number, _, end = max(passes, key=lambda p: p[0])
            days = (ctx.today - end).days
            if days > threshold:
                alerts.append(ctx.alert(
                    "harvest_pass_due", "info", cycle.farm_id, entity,
                    f"Lote «{cycle.plot_name}»: la pasada {number} terminó hace {days} días; "
                    "programa la siguiente o cierra el ciclo",
                    cycle.plot_id, cycle.plot_name, days, threshold, end,
                ))
        else:
            estimate = estimated_harvest(flowering.get(cycle.cycle_id))
            if estimate is not None and estimate < ctx.today:
                alerts.append(ctx.alert(
                    "harvest_pass_due", "info", cycle.farm_id, entity,
                    f"Lote «{cycle.plot_name}»: la floración estimaba la cosecha para el {format_date(estimate)}; "
                    "abre la primera pasada",
                    cycle.plot_id, cycle.plot_name, (ctx.today - estimate).days, None, estimate,
                ))
    return alerts


# ═══════════════════════════════════════════════════════════════════════════
# Desvíos (medium, §4.2)
# ═══════════════════════════════════════════════════════════════════════════


def cycle_inactive(ctx: Context) -> list[Alert]:
    """Ciclo activo sin ningún registro (labor, clima, monitoreo, cosecha) en N días."""
    cycles = ctx.active_cycles()
    ids = [c.cycle_id for c in cycles]
    if not ids:
        return []
    last: dict[int, date] = {}

    def keep(rows):
        for cycle_id, day in rows:
            if day is not None and (cycle_id not in last or day > last[cycle_id]):
                last[cycle_id] = day

    for model, column in CYCLE_LABORS.values():
        keep(ctx.db.query(model.crop_cycle_id, func.max(column)).filter(model.crop_cycle_id.in_(ids))
             .group_by(model.crop_cycle_id).all())
    keep(ctx.db.query(Harvest.crop_cycle_id, func.max(func.coalesce(Harvest.end_date, Harvest.start_date)))
         .filter(Harvest.crop_cycle_id.in_(ids)).group_by(Harvest.crop_cycle_id).all())
    keep(ctx.db.query(Harvest.crop_cycle_id, func.max(HarvestWork.work_date))
         .join(HarvestWork, HarvestWork.harvest_id == Harvest.id)
         .filter(Harvest.crop_cycle_id.in_(ids)).group_by(Harvest.crop_cycle_id).all())
    # El clima de la finca cuenta para todos sus lotes; el de un lote, solo para él
    farm_climate = dict(
        ctx.db.query(ClimateRecord.farm_id, func.max(ClimateRecord.record_date))
        .filter(ClimateRecord.farm_id.in_(ctx.farm_ids), ClimateRecord.plot_id.is_(None))
        .group_by(ClimateRecord.farm_id).all()
    )
    plot_climate = dict(
        ctx.db.query(ClimateRecord.plot_id, func.max(ClimateRecord.record_date))
        .filter(ClimateRecord.farm_id.in_(ctx.farm_ids), ClimateRecord.plot_id.isnot(None))
        .group_by(ClimateRecord.plot_id).all()
    )
    alerts = []
    for cycle in cycles:
        threshold = ctx.plot_value(cycle.plot_id, cycle.farm_id, "inactivity_alert_days")
        if threshold is None:
            continue
        candidates = [cycle.start, last.get(cycle.cycle_id), farm_climate.get(cycle.farm_id), plot_climate.get(cycle.plot_id)]
        since = max(d for d in candidates if d is not None and d >= cycle.start)
        days = (ctx.today - since).days
        if days > threshold:
            alerts.append(ctx.alert(
                "cycle_inactive", "medium", cycle.farm_id, {"plot_id": cycle.plot_id, "crop_cycle_id": cycle.cycle_id},
                f"Lote «{cycle.plot_name}» · ciclo {cycle.number}: {days} días sin registros",
                cycle.plot_id, cycle.plot_name, days, threshold, since,
            ))
    return alerts


def humidity_out_of_range(ctx: Context) -> list[Alert]:
    rows = (
        ctx.db.query(Drying.id, Drying.farm_id, Drying.end_date, Drying.final_humidity_pct)
        .filter(
            Drying.farm_id.in_(ctx.farm_ids),
            Drying.status == DryingStatusEnum.completed,
            Drying.end_date > ctx.today - timedelta(days=RECENT_DAYS),
        ).all()
    )
    alerts = []
    for drying_id, farm_id, end, humidity in rows:
        low = ctx.farm_value(farm_id, "min_final_humidity")
        high = ctx.farm_value(farm_id, "max_final_humidity")
        if (low is not None and humidity < low) or (high is not None and humidity > high):
            limit = low if low is not None and humidity < low else high
            alerts.append(ctx.alert(
                "humidity_out_of_range", "medium", farm_id, {"drying_id": drying_id},
                f"Secado {drying_id} cerró con {_number(humidity)} % de humedad "
                f"(rango {_number(low or 0)}–{_number(high or 100)} %)",
                value=humidity, threshold=limit, since=end,
            ))
    return alerts


FERMENTATION_HOURS = func.extract("epoch", WetProcessing.fermentation_end - WetProcessing.fermentation_start) / 3600


def fermentation_out_of_range(ctx: Context) -> list[Alert]:
    rows = (
        ctx.db.query(WetProcessing.id, WetProcessing.farm_id, WetProcessing.fermentation_end, FERMENTATION_HOURS)
        .filter(
            WetProcessing.farm_id.in_(ctx.farm_ids),
            WetProcessing.fermentation_start.isnot(None),
            WetProcessing.fermentation_end.isnot(None),
            WetProcessing.fermentation_end > ctx.now - timedelta(days=RECENT_DAYS),
        ).all()
    )
    alerts = []
    for wet_id, farm_id, end, hours in rows:
        hours = Decimal(str(round(float(hours), 1)))
        low = ctx.farm_value(farm_id, "min_fermentation_hours")
        high = ctx.farm_value(farm_id, "max_fermentation_hours")
        if (low is not None and hours < low) or (high is not None and hours > high):
            limit = low if low is not None and hours < low else high
            alerts.append(ctx.alert(
                "fermentation_out_of_range", "medium", farm_id, {"wet_processing_id": wet_id},
                f"Beneficio {wet_id}: {_number(hours)} h de fermentación "
                f"(rango {_number(low or 0)}–{_number(high or 720)} h)",
                value=hours, threshold=limit, since=end.astimezone(BUSINESS_TZ).date(),
            ))
    return alerts


def harvest_without_quality(ctx: Context) -> list[Alert]:
    evaluated = ctx.db.query(QualityEval.harvest_id).filter(QualityEval.stage == QualityStageEnum.cherry)
    rows = (
        ctx.db.query(Harvest.id, Harvest.pass_number, Harvest.end_date, Plot.id, Plot.name, Plot.farm_id)
        .join(CropCycle, Harvest.crop_cycle_id == CropCycle.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .filter(
            Plot.farm_id.in_(ctx.farm_ids),
            Harvest.status == HarvestStatusEnum.closed,
            Harvest.end_date > ctx.today - timedelta(days=RECENT_DAYS),
            Harvest.id.notin_(evaluated),
        ).all()
    )
    return [
        ctx.alert(
            "harvest_without_quality", "medium", farm_id, {"harvest_id": harvest_id},
            f"Lote «{plot_name}» · pasada {number}: cerrada sin evaluación en cereza",
            plot_id, plot_name, since=end,
        )
        for harvest_id, number, end, plot_id, plot_name, farm_id in rows
    ]


def drying_without_quality(ctx: Context) -> list[Alert]:
    evaluated = ctx.db.query(QualityEval.drying_id).filter(
        QualityEval.stage == QualityStageEnum.parchment, QualityEval.drying_id.isnot(None)
    )
    rows = (
        ctx.db.query(Drying.id, Drying.farm_id, Drying.end_date)
        .filter(
            Drying.farm_id.in_(ctx.farm_ids),
            Drying.status == DryingStatusEnum.completed,
            Drying.end_date < ctx.today - timedelta(days=QUALITY_GRACE_DAYS),
            Drying.end_date >= ctx.today - timedelta(days=QUALITY_GRACE_DAYS + RECENT_DAYS),
            Drying.id.notin_(evaluated),
        ).all()
    )
    return [
        ctx.alert(
            "drying_without_quality", "medium", farm_id, {"drying_id": drying_id},
            f"Secado {drying_id}: cerrado hace {(ctx.today - end).days} días sin evaluación en pergamino",
            value=(ctx.today - end).days, threshold=QUALITY_GRACE_DAYS, since=end,
        )
        for drying_id, farm_id, end in rows
    ]


def drying_yields(db: Session, farm_ids: list[int], date_from: date, date_to: date) -> list[tuple]:
    """(secado, finca, fin, pergamino seco, cereza trazada) de los secados cerrados en el rango."""
    traced = traced_cherry_select().subquery()
    return (
        db.query(Drying.id, Drying.farm_id, Drying.end_date, Drying.output_kg, func.sum(traced.c.cherry_kg))
        .join(traced, traced.c.drying_id == Drying.id)
        .filter(
            Drying.farm_id.in_(farm_ids),
            Drying.status == DryingStatusEnum.completed,
            Drying.end_date >= date_from,
            Drying.end_date <= date_to,
        )
        .group_by(Drying.id)
        .all()
    )


def yield_pct(output, cherry) -> Optional[Decimal]:
    return (Decimal(output) * 100 / Decimal(cherry)).quantize(Decimal("0.1")) if cherry else None


def yield_below_history(ctx: Context) -> list[Alert]:
    """Rendimiento de un secado reciente frente al de la finca en el año anterior."""
    window_start = ctx.today - timedelta(days=RECENT_DAYS)
    history: dict[int, list] = {}
    for _, farm_id, _, output, cherry in drying_yields(
        ctx.db, ctx.farm_ids, window_start - timedelta(days=HISTORY_DAYS), window_start - timedelta(days=1)
    ):
        entry = history.setdefault(farm_id, [Decimal(0), Decimal(0), 0])
        entry[0] += output
        entry[1] += Decimal(cherry)
        entry[2] += 1
    alerts = []
    for drying_id, farm_id, end, output, cherry in drying_yields(ctx.db, ctx.farm_ids, window_start, ctx.today):
        output_kg, cherry_kg, count = history.get(farm_id, (0, 0, 0))
        if count < MIN_HISTORY_DRYINGS:
            continue
        reference = yield_pct(output_kg, cherry_kg)
        current = yield_pct(output, cherry)
        if current is not None and reference is not None and current < reference - YIELD_DROP_POINTS:
            alerts.append(ctx.alert(
                "yield_below_history", "medium", farm_id, {"drying_id": drying_id},
                f"Secado {drying_id}: rendimiento {_number(current)} % frente a {_number(reference)} % "
                "de la finca en el último año",
                value=current, threshold=reference - YIELD_DROP_POINTS, since=end,
            ))
    return alerts


# ═══════════════════════════════════════════════════════════════════════════
# Riesgos (high, §4.3)
# ═══════════════════════════════════════════════════════════════════════════


def latest_monitorings(db: Session, cycle_ids: list[int], column) -> dict[int, tuple]:
    """Último muestreo de cada ciclo con valor en la columna: (fecha, valor)."""
    if not cycle_ids:
        return {}
    rows = (
        db.query(PestMonitoring.crop_cycle_id, PestMonitoring.monitoring_date, column)
        .filter(PestMonitoring.crop_cycle_id.in_(cycle_ids), column.isnot(None))
        .order_by(PestMonitoring.crop_cycle_id, PestMonitoring.monitoring_date.desc(), PestMonitoring.id.desc())
        .distinct(PestMonitoring.crop_cycle_id)
        .all()
    )
    return {cycle_id: (day, value) for cycle_id, day, value in rows}


def broca_above_threshold(ctx: Context) -> list[Alert]:
    cycles = ctx.active_cycles()
    latest = latest_monitorings(ctx.db, [c.cycle_id for c in cycles], PestMonitoring.broca_pct)
    alerts = []
    for cycle in cycles:
        if cycle.cycle_id not in latest:
            continue
        day, broca = latest[cycle.cycle_id]
        threshold = ctx.plot_value(cycle.plot_id, cycle.farm_id, "broca_alert_pct")
        if threshold is not None and broca >= threshold:
            alerts.append(ctx.alert(
                "broca_above_threshold", "high", cycle.farm_id, {"plot_id": cycle.plot_id, "crop_cycle_id": cycle.cycle_id},
                f"Lote «{cycle.plot_name}»: broca en {_number(broca)} % (umbral {_number(threshold)} %), "
                f"último muestreo del {format_date(day)}",
                cycle.plot_id, cycle.plot_name, broca, threshold, day,
            ))
    return alerts


def drying_too_long(ctx: Context) -> list[Alert]:
    rows = (
        ctx.db.query(Drying.id, Drying.farm_id, Drying.start_date)
        .filter(Drying.farm_id.in_(ctx.farm_ids), Drying.status == DryingStatusEnum.in_progress).all()
    )
    alerts = []
    for drying_id, farm_id, start in rows:
        threshold = ctx.farm_value(farm_id, "max_drying_days")
        days = (ctx.today - start).days
        if threshold is not None and days > threshold:
            alerts.append(ctx.alert(
                "drying_too_long", "high", farm_id, {"drying_id": drying_id},
                f"Secado {drying_id} lleva {days} días (umbral {threshold})",
                value=days, threshold=threshold, since=start,
            ))
    return alerts


def processing_stalled(ctx: Context) -> list[Alert]:
    """La única alerta en tiempo real: fermentación en curso por encima del máximo."""
    rows = (
        ctx.db.query(WetProcessing.id, WetProcessing.farm_id, WetProcessing.fermentation_start)
        .filter(
            WetProcessing.farm_id.in_(ctx.farm_ids),
            WetProcessing.status == WetProcessingStatusEnum.in_progress,
            WetProcessing.fermentation_start.isnot(None),
            WetProcessing.fermentation_end.is_(None),
        ).all()
    )
    alerts = []
    for wet_id, farm_id, start in rows:
        threshold = ctx.farm_value(farm_id, "max_fermentation_hours")
        hours = Decimal(str(round((ctx.now - start).total_seconds() / 3600, 1)))
        if threshold is not None and hours > threshold:
            alerts.append(ctx.alert(
                "processing_stalled", "high", farm_id, {"wet_processing_id": wet_id},
                f"Beneficio {wet_id}: fermentando hace {_number(hours)} h sin lavar (máximo {threshold} h)",
                value=hours, threshold=threshold, since=start.astimezone(BUSINESS_TZ).date(),
            ))
    return alerts


def unpaid_labor(ctx: Context) -> list[Alert]:
    """Una alerta por finca con lo que debe hace más de 15 días (recolección y jornales)."""
    limit = ctx.today - timedelta(days=UNPAID_DAYS)
    works = (
        ctx.db.query(Plot.farm_id, func.count(HarvestWork.id), func.sum(HarvestWork.total_value), func.min(HarvestWork.work_date))
        .join(Harvest, HarvestWork.harvest_id == Harvest.id)
        .join(CropCycle, Harvest.crop_cycle_id == CropCycle.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .filter(Plot.farm_id.in_(ctx.farm_ids), HarvestWork.paid.is_(False), HarvestWork.work_date < limit)
        .group_by(Plot.farm_id).all()
    )
    labors = (
        ctx.db.query(Employee.farm_id, func.count(DayLabor.id), func.sum(DayLabor.daily_value), func.min(DayLabor.labor_date))
        .join(Employee, DayLabor.employee_id == Employee.id)
        .filter(Employee.farm_id.in_(ctx.farm_ids), DayLabor.paid.is_(False), DayLabor.labor_date < limit)
        .group_by(Employee.farm_id).all()
    )
    totals: dict[int, list] = {}
    for farm_id, count, amount, oldest in [*works, *labors]:
        entry = totals.setdefault(farm_id, [0, Decimal(0), oldest])
        entry[0] += count
        entry[1] += amount
        entry[2] = min(entry[2], oldest)
    return [
        ctx.alert(
            "unpaid_labor", "high", farm_id, {"farm_id": farm_id},
            f"{count} pagos pendientes por {money(amount)} con más de {UNPAID_DAYS} días "
            f"(el más antiguo, del {format_date(oldest)})",
            value=amount, threshold=UNPAID_DAYS, since=oldest,
        )
        for farm_id, (count, amount, oldest) in totals.items()
    ]


def harvest_open_too_long(ctx: Context) -> list[Alert]:
    rows = (
        ctx.db.query(Harvest.id, Harvest.pass_number, Harvest.start_date, Plot.id, Plot.name, Plot.farm_id)
        .join(CropCycle, Harvest.crop_cycle_id == CropCycle.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .filter(
            Plot.farm_id.in_(ctx.farm_ids),
            Harvest.status == HarvestStatusEnum.open,
            Harvest.start_date < ctx.today - timedelta(days=HARVEST_OPEN_DAYS),
        ).all()
    )
    return [
        ctx.alert(
            "harvest_open_too_long", "high", farm_id, {"harvest_id": harvest_id},
            f"Lote «{plot_name}» · pasada {number}: abierta hace {(ctx.today - start).days} días; "
            "ciérrala con su total para cuadrar el beneficio",
            plot_id, plot_name, (ctx.today - start).days, HARVEST_OPEN_DAYS, start,
        )
        for harvest_id, number, start, plot_id, plot_name, farm_id in rows
    ]


# Registro: una función por tipo de alerta (§6)
CHECKS: list[Callable[[Context], list[Alert]]] = [
    fertilization_due,
    phytosanitary_due,
    weeding_due,
    irrigation_due,
    harvest_pass_due,
    cycle_inactive,
    humidity_out_of_range,
    fermentation_out_of_range,
    harvest_without_quality,
    drying_without_quality,
    yield_below_history,
    broca_above_threshold,
    drying_too_long,
    processing_stalled,
    unpaid_labor,
    harvest_open_too_long,
]


def build_context(db: Session, farm_ids: list[int], today: Optional[date] = None,
                  now: Optional[datetime] = None) -> Context:
    """Configuraciones de las fincas del alcance y de sus lotes: dos consultas."""
    plots = db.query(Plot.id).filter(Plot.farm_id.in_(farm_ids))
    configs = db.query(AlertConfig).filter(or_(AlertConfig.farm_id.in_(farm_ids), AlertConfig.plot_id.in_(plots))).all()
    return Context(
        db=db,
        farm_ids=farm_ids,
        today=today or business_today(),
        now=now or datetime.now(BUSINESS_TZ),
        farm_names=dict(db.query(Farm.id, Farm.name).filter(Farm.id.in_(farm_ids)).all()),
        farm_configs={c.farm_id: c for c in configs if c.farm_id is not None},
        plot_configs={c.plot_id: c for c in configs if c.plot_id is not None},
    )


def compute_alerts(db: Session, farm_ids: list[int], today: Optional[date] = None,
                   now: Optional[datetime] = None) -> list[Alert]:
    """Alertas activas de las fincas, de la más grave y antigua a la más leve y reciente."""
    if not farm_ids:
        return []
    ctx = build_context(db, farm_ids, today, now)
    alerts: list[Alert] = []
    for check in CHECKS:
        alerts += check(ctx)
    return sorted(alerts, key=lambda a: (SEVERITY_ORDER[a.severity], a.since or ctx.today, a.farm_name, a.message))


