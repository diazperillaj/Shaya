import math
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.api_v1.dashboard.schema import BarChartData, ChartSeries
from app.core.exceptions.domain import DomainError
from app.farm_operations.models import (
    CropCycle,
    DayLabor,
    Drying,
    DryingInput,
    Employee,
    Farm,
    Harvest,
    HarvestWork,
    PestMonitoring,
    Plot,
    QualityEval,
    WetProcessing,
    WetProcessingInput,
)
from app.farm_operations.models.enums import (
    CycleStatusEnum,
    DryingDestinationEnum,
    DryingStatusEnum,
    HarvestStatusEnum,
    PlotStatusEnum,
    QualityStageEnum,
    WetProcessingStatusEnum,
)
from app.farm_operations.services import alerts as alert_service
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.cycle_records import CYCLE_LABORS
from app.farm_operations.services.dates import business_date, business_today
from app.farm_operations.services.seasons import MONTHS, HarvestSpan, group_seasons
from app.farm_operations.services.traceability import traced_cherry_select
from app.models.parchment import Parchment

HISTORY_DAYS = 365
SCORE_BIN = 2          # puntos por barra del histograma de puntajes
HUMIDITY_BINS = [8.0 + 0.5 * i for i in range(13)]   # 8 % … 14 %


def _float(value) -> float:
    return float(value) if value is not None else 0.0


def _optional(value) -> Optional[float]:
    return float(value) if value is not None else None


def chart(labels: list, series: dict[str, list]) -> BarChartData:
    return BarChartData(
        labels=[str(label) for label in labels],
        series=[ChartSeries(name=name, data=[round(float(v), 2) for v in values]) for name, values in series.items()],
    )


def month_keys(date_from: date, date_to: date) -> list[tuple[int, int]]:
    keys, year, month = [], date_from.year, date_from.month
    while (year, month) <= (date_to.year, date_to.month):
        keys.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return keys


def month_label(key: tuple[int, int]) -> str:
    return f"{MONTHS[key[1] - 1]} {key[0]}"


def ratio_pct(part, whole) -> Optional[float]:
    return round(float(part) * 100 / float(whole), 1) if whole else None


class DashboardService:
    """
    Dashboard del módulo de cultivo (dashboards-alertas).

    Mismo dashboard para todos; lo que cambia es el alcance: el
    administrador ve todas las fincas (o una), el caficultor las suyas. Los
    widgets de estado muestran siempre el ahora; los de periodo, el rango.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access
        self.today = business_today()

    # ── Alcance y periodo ─────────────────────────────────────────────────

    def scope(self, farm_id: Optional[int]) -> list[int]:
        if farm_id is not None:
            return [self.access.get_farm(farm_id).id]
        return [row[0] for row in self.access.farms().with_entities(Farm.id).all()]

    def period(self, date_from: Optional[date], date_to: Optional[date]) -> tuple[date, date]:
        """Por defecto, los últimos 12 meses."""
        end = date_to or self.today
        start = date_from or end - timedelta(days=HISTORY_DAYS - 1)
        if start > end:
            raise DomainError("La fecha inicial no puede ser posterior a la final")
        return start, end

    def unit(self, farm_ids: list[int]) -> str:
        """Con una sola finca, las gráficas por unidad van por lote; si no, por finca."""
        return "plot" if len(farm_ids) == 1 else "farm"

    # ── Resumen (KPIs) ────────────────────────────────────────────────────

    def summary(self, farm_id: Optional[int], date_from: Optional[date], date_to: Optional[date]) -> dict:
        db, farm_ids = self.db, self.scope(farm_id)
        start, end = self.period(date_from, date_to)

        plots = db.query(Plot).filter(Plot.farm_id.in_(farm_ids), Plot.status == PlotStatusEnum.active)
        area = (
            plots.with_entities(Plot.variety, func.coalesce(func.sum(Plot.area), 0))
            .group_by(Plot.variety).order_by(func.sum(Plot.area).desc().nullslast()).all()
        )
        wet = (
            db.query(func.count(func.distinct(WetProcessing.id)), func.sum(WetProcessingInput.cherry_kg),
                     func.min(WetProcessing.created_at))
            .join(WetProcessingInput, WetProcessingInput.wet_processing_id == WetProcessing.id)
            .filter(WetProcessing.farm_id.in_(farm_ids), WetProcessing.status == WetProcessingStatusEnum.in_progress)
            .one()
        )
        drying = (
            db.query(func.count(func.distinct(Drying.id)), func.sum(DryingInput.wet_kg), func.min(Drying.start_date))
            .join(DryingInput, DryingInput.drying_id == Drying.id)
            .filter(Drying.farm_id.in_(farm_ids), Drying.status == DryingStatusEnum.in_progress)
            .one()
        )
        yields = alert_service.drying_yields(db, farm_ids, start, end)
        history = alert_service.drying_yields(db, farm_ids, start - timedelta(days=HISTORY_DAYS), start - timedelta(days=1))
        score = (
            db.query(func.avg(QualityEval.score), func.count(QualityEval.id))
            .join(Drying, QualityEval.drying_id == Drying.id)
            .filter(Drying.farm_id.in_(farm_ids), QualityEval.stage == QualityStageEnum.parchment,
                    QualityEval.score.isnot(None), QualityEval.eval_date.between(start, end))
            .one()
        )
        return {
            "period": {"date_from": start, "date_to": end},
            "farms_active": db.query(Farm).filter(Farm.id.in_(farm_ids), Farm.active.is_(True)).count(),
            "plots_active": plots.count(),
            "area_by_variety": [{"variety": variety, "area_ha": float(total)} for variety, total in area],
            "cycles_active": (
                db.query(CropCycle).join(Plot, CropCycle.plot_id == Plot.id)
                .filter(Plot.farm_id.in_(farm_ids), CropCycle.status == CycleStatusEnum.active).count()
            ),
            "harvests_open": (
                self._harvests(farm_ids).filter(Harvest.status == HarvestStatusEnum.open).count()
            ),
            "wet_in_progress": {
                "count": wet[0], "kg": _float(wet[1]),
                "oldest_days": (self.today - business_date(wet[2])).days if wet[2] else None,
            },
            "drying_in_progress": {
                "count": drying[0], "kg": _float(drying[1]),
                "oldest_days": (self.today - drying[2]).days if drying[2] else None,
            },
            "stored_parchment_kg": _float(self._stored(farm_ids).with_entities(func.sum(Drying.output_kg)).scalar()),
            "pending_payments": self._pending_payments(farm_ids),
            "stored_dryings": [
                {"drying_id": d.id, "farm_id": d.farm_id, "farm_name": d.farm.name, "end_date": d.end_date,
                 "output_kg": float(d.output_kg), "days": (self.today - d.end_date).days}
                for d in self._stored(farm_ids).order_by(Drying.end_date, Drying.id).limit(10)
            ],
            "cherry_kg": _float(
                self._harvests(farm_ids)
                .filter(Harvest.status == HarvestStatusEnum.closed, Harvest.end_date.between(start, end))
                .with_entities(func.sum(Harvest.total_cherry_kg)).scalar()
            ),
            "parchment_kg": float(sum((row[3] for row in yields), Decimal(0))),
            "yield_pct": ratio_pct(sum((r[3] for r in yields), Decimal(0)), sum((r[4] for r in yields), Decimal(0))),
            "yield_history_pct": ratio_pct(sum((r[3] for r in history), Decimal(0)), sum((r[4] for r in history), Decimal(0))),
            "harvest_cost": _float(
                db.query(func.sum(HarvestWork.total_value))
                .join(Harvest, HarvestWork.harvest_id == Harvest.id)
                .filter(Harvest.id.in_(self._harvests(farm_ids).with_entities(Harvest.id)),
                        Harvest.status == HarvestStatusEnum.closed, Harvest.end_date.between(start, end))
                .scalar()
            ),
            "score_avg": round(float(score[0]), 1) if score[0] is not None else None,
            "evaluations": score[1],
        }

    def _harvests(self, farm_ids: list[int]):
        return (
            self.db.query(Harvest)
            .join(CropCycle, Harvest.crop_cycle_id == CropCycle.id)
            .join(Plot, CropCycle.plot_id == Plot.id)
            .filter(Plot.farm_id.in_(farm_ids))
        )

    def _stored(self, farm_ids: list[int]):
        return self.db.query(Drying).filter(
            Drying.farm_id.in_(farm_ids),
            Drying.status == DryingStatusEnum.completed,
            Drying.destination == DryingDestinationEnum.stored,
        )

    def _pending_payments(self, farm_ids: list[int]) -> float:
        works = (
            self.db.query(func.sum(HarvestWork.total_value))
            .filter(HarvestWork.paid.is_(False),
                    HarvestWork.harvest_id.in_(self._harvests(farm_ids).with_entities(Harvest.id)))
            .scalar()
        )
        labors = (
            self.db.query(func.sum(DayLabor.daily_value))
            .join(Employee, DayLabor.employee_id == Employee.id)
            .filter(Employee.farm_id.in_(farm_ids), DayLabor.paid.is_(False))
            .scalar()
        )
        return _float(works) + _float(labors)

    # ── Alertas ───────────────────────────────────────────────────────────

    def alerts(self, farm_id: Optional[int]) -> list[dict]:
        return [alert.as_dict() for alert in alert_service.compute_alerts(self.db, self.scope(farm_id))]

    # ── Producción ────────────────────────────────────────────────────────

    def _traced_rows(self, farm_ids: list[int], drying_filter) -> list:
        """Por secado y lote de origen: pergamino del secado y cereza trazada desde ese lote."""
        traced = traced_cherry_select().subquery()
        return (
            self.db.query(Drying.id, Drying.output_kg, Drying.farm_id, Farm.name,
                          traced.c.plot_id, traced.c.plot_name, traced.c.variety, traced.c.cherry_kg)
            .join(traced, traced.c.drying_id == Drying.id)
            .join(Farm, Drying.farm_id == Farm.id)
            .filter(Drying.farm_id.in_(farm_ids), drying_filter)
            .all()
        )

    @staticmethod
    def _shares(rows) -> dict[int, list]:
        """Reparte cada secado entre sus lotes de origen según la cereza trazada."""
        by_drying: dict[int, list] = defaultdict(list)
        for row in rows:
            by_drying[row[0]].append(row)
        shares = {}
        for drying_id, items in by_drying.items():
            total = sum((Decimal(item[7]) for item in items), Decimal(0))
            shares[drying_id] = [(item, Decimal(item[7]) / total if total else Decimal(0)) for item in items]
        return shares

    @staticmethod
    def _unit_key(unit: str, row) -> tuple:
        return (row[4], row[5]) if unit == "plot" else (row[2], row[3])

    @staticmethod
    def _labels(keys: Iterable[tuple]) -> list[str]:
        """Nombre de cada unidad; si dos se llaman igual (un lote renovado), se distinguen por su id."""
        keys = list(keys)
        names = [name for _, name in keys]
        return [name if names.count(name) == 1 else f"{name} · {key}" for key, name in keys]

    def production(self, farm_id: Optional[int], date_from: Optional[date], date_to: Optional[date]) -> dict:
        db, farm_ids = self.db, self.scope(farm_id)
        start, end = self.period(date_from, date_to)
        unit = self.unit(farm_ids)
        months = month_keys(start, end)

        cherry_month = dict(
            self._harvests(farm_ids)
            .filter(Harvest.status == HarvestStatusEnum.closed, Harvest.end_date.between(start, end))
            .with_entities(func.date_trunc("month", Harvest.end_date), func.sum(Harvest.total_cherry_kg))
            .group_by(func.date_trunc("month", Harvest.end_date)).all()
        )
        parchment_month = dict(
            db.query(func.date_trunc("month", Drying.end_date), func.sum(Drying.output_kg))
            .filter(Drying.farm_id.in_(farm_ids), Drying.status == DryingStatusEnum.completed,
                    Drying.end_date.between(start, end))
            .group_by(func.date_trunc("month", Drying.end_date)).all()
        )
        month_of = lambda moment: (moment.year, moment.month)  # noqa: E731
        cherry_by = {month_of(k): v for k, v in cherry_month.items()}
        parchment_by = {month_of(k): v for k, v in parchment_month.items()}

        completed = (Drying.status == DryingStatusEnum.completed) & Drying.end_date.between(start, end)
        shares = self._shares(self._traced_rows(farm_ids, completed))
        output_by_unit: dict[tuple, Decimal] = defaultdict(Decimal)
        cherry_by_unit: dict[tuple, Decimal] = defaultdict(Decimal)
        output_by_variety: dict[str, Decimal] = defaultdict(Decimal)
        for items in shares.values():
            for row, share in items:
                output = Decimal(row[1]) * share
                key = self._unit_key(unit, row)
                output_by_unit[key] += output
                cherry_by_unit[key] += Decimal(row[7])
                output_by_variety[row[6]] += output
        units = sorted(output_by_unit, key=lambda k: output_by_unit[k], reverse=True)
        varieties = sorted(output_by_variety, key=lambda v: output_by_variety[v], reverse=True)

        history = alert_service.drying_yields(db, farm_ids, start - timedelta(days=HISTORY_DAYS), start - timedelta(days=1))

        works = (
            db.query(func.date_trunc("month", HarvestWork.work_date), func.sum(HarvestWork.total_value),
                     func.sum(HarvestWork.kg_collected))
            .filter(HarvestWork.harvest_id.in_(self._harvests(farm_ids).with_entities(Harvest.id)),
                    HarvestWork.kg_collected.isnot(None), HarvestWork.work_date.between(start, end))
            .group_by(func.date_trunc("month", HarvestWork.work_date)).all()
        )
        cost_by = {month_of(k): (value / kg if kg else None) for k, value, kg in works}

        in_inventory = (
            db.query(func.sum(Parchment.remaining_quantity))
            .join(Drying, Parchment.drying_id == Drying.id)
            .filter(Drying.farm_id.in_(farm_ids)).scalar()
        )
        summary_wet = (
            db.query(func.sum(WetProcessingInput.cherry_kg))
            .join(WetProcessing, WetProcessingInput.wet_processing_id == WetProcessing.id)
            .filter(WetProcessing.farm_id.in_(farm_ids), WetProcessing.status == WetProcessingStatusEnum.in_progress)
            .scalar()
        )
        summary_drying = (
            db.query(func.sum(DryingInput.wet_kg))
            .join(Drying, DryingInput.drying_id == Drying.id)
            .filter(Drying.farm_id.in_(farm_ids), Drying.status == DryingStatusEnum.in_progress)
            .scalar()
        )
        stored = self._stored(farm_ids).with_entities(func.sum(Drying.output_kg)).scalar()

        return {
            "unit": unit,
            "monthly": chart([month_label(m) for m in months], {
                "Cereza (kg)": [_float(cherry_by.get(m)) for m in months],
                "Pergamino seco (kg)": [_float(parchment_by.get(m)) for m in months],
            }),
            "by_unit": chart(self._labels(units), {"Pergamino seco (kg)": [output_by_unit[k] for k in units]}),
            "yield_by_unit": chart(self._labels(units), {
                "Rendimiento (%)": [ratio_pct(output_by_unit[k], cherry_by_unit[k]) or 0 for k in units],
            }),
            "yield_reference_pct": ratio_pct(sum((r[3] for r in history), Decimal(0)),
                                             sum((r[4] for r in history), Decimal(0))),
            "by_variety": chart(varieties, {"Pergamino seco (kg)": [output_by_variety[v] for v in varieties]}),
            "picking_cost": chart(
                [month_label(m) for m in months if m in cost_by],
                {"COP por kg de cereza": [cost_by[m] for m in months if m in cost_by]},
            ),
            "pipeline": chart(["Ahora"], {
                "En beneficio (kg cereza)": [_float(summary_wet)],
                "En secado (kg lavado)": [_float(summary_drying)],
                "Guardado en finca (kg pergamino)": [_float(stored)],
                "En inventario (kg pergamino)": [_float(in_inventory)],
            }),
        }

    # ── Calidad y sanidad ─────────────────────────────────────────────────

    def quality(self, farm_id: Optional[int], date_from: Optional[date], date_to: Optional[date]) -> dict:
        db, farm_ids = self.db, self.scope(farm_id)
        start, end = self.period(date_from, date_to)
        unit = self.unit(farm_ids)

        evals = (
            db.query(QualityEval.drying_id, QualityEval.score, QualityEval.defects_pct, QualityEval.eval_date)
            .join(Drying, QualityEval.drying_id == Drying.id)
            .filter(Drying.farm_id.in_(farm_ids), QualityEval.stage == QualityStageEnum.parchment,
                    QualityEval.eval_date.between(start, end))
            .all()
        )
        evaluated = {e[0] for e in evals}
        shares = self._shares(self._traced_rows(farm_ids, Drying.id.in_(evaluated))) if evaluated else {}

        # Puntaje y defectos ponderados por la cereza que cada lote aportó a cada secado
        acc = {"variety": defaultdict(lambda: [0.0, 0.0]), "score": defaultdict(lambda: [0.0, 0.0]),
               "defects": defaultdict(lambda: [0.0, 0.0])}
        for drying_id, score, defects, _ in evals:
            for row, share in shares.get(drying_id, []):
                weight = float(row[7]) * 1.0
                key = self._unit_key(unit, row)
                if score is not None:
                    acc["variety"][row[6]][0] += float(score) * weight
                    acc["variety"][row[6]][1] += weight
                    acc["score"][key][0] += float(score) * weight
                    acc["score"][key][1] += weight
                if defects is not None:
                    acc["defects"][key][0] += float(defects) * weight
                    acc["defects"][key][1] += weight

        def averages(table) -> dict:
            return {k: round(total / weight, 1) for k, (total, weight) in table.items() if weight}

        by_variety = averages(acc["variety"])
        score_unit, defects_unit = averages(acc["score"]), averages(acc["defects"])
        units = sorted(set(score_unit) | set(defects_unit), key=lambda k: score_unit.get(k, 0), reverse=True)
        varieties = sorted(by_variety, key=lambda v: by_variety[v], reverse=True)

        scores = [float(e[1]) for e in evals if e[1] is not None]
        bins = self._score_bins(scores)
        months = month_keys(start, end)
        monthly: dict[tuple, list] = defaultdict(list)
        for _, score, _, day in evals:
            if score is not None:
                monthly[(day.year, day.month)].append(float(score))
        evolution_months = [m for m in months if m in monthly]

        broca, roya, threshold = self._health(farm_ids, unit)
        health_units = sorted(set(broca) | set(roya), key=lambda k: broca.get(k, 0), reverse=True)

        humidity = [
            float(h) for (h,) in db.query(Drying.final_humidity_pct).filter(
                Drying.farm_id.in_(farm_ids), Drying.status == DryingStatusEnum.completed,
                Drying.end_date.between(start, end),
            )
        ]
        ctx = alert_service.build_context(db, farm_ids)
        if len(farm_ids) == 1:
            band = (ctx.farm_value(farm_ids[0], "min_final_humidity"), ctx.farm_value(farm_ids[0], "max_final_humidity"))
        else:
            band = (alert_service.DEFAULTS["min_final_humidity"], alert_service.DEFAULTS["max_final_humidity"])

        return {
            "unit": unit,
            "score_distribution": chart([label for label, _ in bins], {"Secados": [count for _, count in bins]}),
            "score_by_variety": chart(varieties, {"Puntaje promedio": [by_variety[v] for v in varieties]}),
            "score_defects_by_unit": chart(self._labels(units), {
                "Puntaje promedio": [score_unit.get(k, 0) for k in units],
                "Defectos (%)": [defects_unit.get(k, 0) for k in units],
            }),
            "score_evolution": chart([month_label(m) for m in evolution_months], {
                "Puntaje promedio": [round(sum(monthly[m]) / len(monthly[m]), 1) for m in evolution_months],
            }),
            "broca_by_unit": chart(self._labels(health_units), {
                "Broca (%)": [broca.get(k, 0) for k in health_units],
                "Umbral (%)": [threshold.get(k, 0) for k in health_units],
            }),
            "roya_by_unit": chart(self._labels(health_units), {"Roya (%)": [roya.get(k, 0) for k in health_units]}),
            "humidity_distribution": self._humidity_bins(humidity),
            "humidity_range": (_optional(band[0]), _optional(band[1])),
        }

    @staticmethod
    def _score_bins(scores: list[float]) -> list[tuple[str, int]]:
        if not scores:
            return []
        low = int(math.floor(min(scores) / SCORE_BIN) * SCORE_BIN)
        high = int(math.floor(max(scores) / SCORE_BIN) * SCORE_BIN)
        bins = []
        for start in range(low, high + 1, SCORE_BIN):
            count = sum(start <= s < start + SCORE_BIN for s in scores)
            bins.append((f"{start}–{start + SCORE_BIN}", count))
        return bins

    @staticmethod
    def _humidity_bins(values: list[float]) -> BarChartData:
        edges = HUMIDITY_BINS
        labels = [f"< {edges[0]:g}".replace(".", ",")]
        counts = [sum(v < edges[0] for v in values)]
        for low, high in zip(edges, edges[1:]):
            labels.append(f"{low:g}–{high:g}".replace(".", ","))
            counts.append(sum(low <= v < high for v in values))
        labels.append(f"≥ {edges[-1]:g}".replace(".", ","))
        counts.append(sum(v >= edges[-1] for v in values))
        return chart(labels, {"Secados": counts})

    def _health(self, farm_ids: list[int], unit: str):
        """Último muestreo de broca y roya de cada ciclo activo; por finca, el mayor de sus lotes."""
        ctx = alert_service.build_context(self.db, farm_ids)
        cycles = ctx.active_cycles()
        ids = [c.cycle_id for c in cycles]
        broca_latest = alert_service.latest_monitorings(self.db, ids, PestMonitoring.broca_pct)
        roya_latest = alert_service.latest_monitorings(self.db, ids, PestMonitoring.roya_pct)
        farm_names = ctx.farm_names
        broca, roya, threshold = {}, {}, {}
        for cycle in cycles:
            key = (cycle.plot_id, cycle.plot_name) if unit == "plot" else (cycle.farm_id, farm_names[cycle.farm_id])
            limit = (ctx.plot_value(cycle.plot_id, cycle.farm_id, "broca_alert_pct") if unit == "plot"
                     else ctx.farm_value(cycle.farm_id, "broca_alert_pct"))
            if cycle.cycle_id in broca_latest:
                value = float(broca_latest[cycle.cycle_id][1])
                broca[key] = max(broca.get(key, 0.0), value)
                threshold[key] = _float(limit)
            if cycle.cycle_id in roya_latest:
                roya[key] = max(roya.get(key, 0.0), float(roya_latest[cycle.cycle_id][1]))
                threshold.setdefault(key, _float(limit))
        return broca, roya, threshold

    # ── Temporadas ────────────────────────────────────────────────────────

    def periods(self, farm_id: Optional[int], plot_id: Optional[int]) -> list[dict]:
        query = self._harvests(self.scope(farm_id))
        if plot_id is not None:
            query = query.filter(Plot.id == self.access.get_plot(plot_id).id)
        last_work = (
            self.db.query(func.max(HarvestWork.work_date))
            .filter(HarvestWork.harvest_id == Harvest.id)
            .correlate(Harvest)
            .scalar_subquery()
        )
        spans = [
            HarvestSpan(start, end, total, last)
            for start, end, total, last in query.with_entities(
                Harvest.start_date, Harvest.end_date, Harvest.total_cherry_kg, last_work
            )
        ]
        return [
            {"label": s.label, "date_from": s.date_from, "date_to": s.date_to, "harvests": s.harvests,
             "cherry_kg": float(s.cherry_kg), "open": s.open}
            for s in group_seasons(spans, self.today)
        ]

    # ── Estado de los ciclos (caficultor) ─────────────────────────────────

    def cycles(self, farm_id: Optional[int]) -> list[dict]:
        db, farm_ids = self.db, self.scope(farm_id)
        ctx = alert_service.build_context(db, farm_ids)
        cycles = ctx.active_cycles()
        ids = [c.cycle_id for c in cycles]
        last: dict[int, tuple] = {}
        for kind, (model, column) in CYCLE_LABORS.items():
            if not ids:
                break
            for cycle_id, day in (
                db.query(model.crop_cycle_id, func.max(column)).filter(model.crop_cycle_id.in_(ids))
                .group_by(model.crop_cycle_id).all()
            ):
                if cycle_id not in last or day > last[cycle_id][1]:
                    last[cycle_id] = (kind, day)
        status: dict[int, str] = {}
        if ids:
            for cycle_id, open_count, total in (
                db.query(Harvest.crop_cycle_id,
                         func.count().filter(Harvest.status == HarvestStatusEnum.open), func.count())
                .filter(Harvest.crop_cycle_id.in_(ids)).group_by(Harvest.crop_cycle_id).all()
            ):
                status[cycle_id] = "open" if open_count else "harvested" if total else "waiting"
        flowering = alert_service.main_flowering(ctx, ids)
        counts: dict[int, int] = defaultdict(int)
        for alert in alert_service.compute_alerts(db, farm_ids):
            if alert.plot_id is not None:
                counts[alert.plot_id] += 1
        return [
            {
                "crop_cycle_id": c.cycle_id, "cycle_number": c.number, "plot_id": c.plot_id, "plot_name": c.plot_name,
                "farm_id": c.farm_id, "farm_name": ctx.farm_names[c.farm_id], "start_date": c.start,
                "days": (self.today - c.start).days,
                "last_labor": {"kind": last[c.cycle_id][0], "date": last[c.cycle_id][1]} if c.cycle_id in last else None,
                "harvest_status": status.get(c.cycle_id, "waiting"),
                "estimated_harvest": alert_service.estimated_harvest(flowering.get(c.cycle_id)),
                "alerts": counts.get(c.plot_id, 0),
            }
            for c in cycles
        ]

    # ── Ranking de fincas (administrador) ─────────────────────────────────

    def farms(self, date_from: Optional[date], date_to: Optional[date]) -> list[dict]:
        db, farm_ids = self.db, self.scope(None)
        start, end = self.period(date_from, date_to)
        rows: dict[int, dict] = {}
        for farm_id, name in db.query(Farm.id, Farm.name).filter(Farm.id.in_(farm_ids)).order_by(Farm.name):
            rows[farm_id] = {
                "farm_id": farm_id, "farm_name": name, "plots_active": 0, "cherry_kg": 0.0, "parchment_kg": 0.0,
                "yield_pct": None, "score_avg": None, "alerts_high": 0, "alerts_medium": 0, "alerts_info": 0,
                "broca_pct": None, "roya_pct": None, "broca_threshold": None, "stored_kg": 0.0,
            }
        for farm_id, count in (
            db.query(Plot.farm_id, func.count()).filter(Plot.farm_id.in_(farm_ids), Plot.status == PlotStatusEnum.active)
            .group_by(Plot.farm_id)
        ):
            rows[farm_id]["plots_active"] = count
        for farm_id, total in (
            self._harvests(farm_ids)
            .filter(Harvest.status == HarvestStatusEnum.closed, Harvest.end_date.between(start, end))
            .with_entities(Plot.farm_id, func.sum(Harvest.total_cherry_kg)).group_by(Plot.farm_id)
        ):
            rows[farm_id]["cherry_kg"] = _float(total)
        produced: dict[int, list] = defaultdict(lambda: [Decimal(0), Decimal(0)])
        for _, farm_id, _, output, cherry in alert_service.drying_yields(db, farm_ids, start, end):
            produced[farm_id][0] += output
            produced[farm_id][1] += Decimal(cherry)
        for farm_id, (output, cherry) in produced.items():
            rows[farm_id]["parchment_kg"] = float(output)
            rows[farm_id]["yield_pct"] = ratio_pct(output, cherry)
        for farm_id, score in (
            db.query(Drying.farm_id, func.avg(QualityEval.score))
            .join(Drying, QualityEval.drying_id == Drying.id)
            .filter(Drying.farm_id.in_(farm_ids), QualityEval.stage == QualityStageEnum.parchment,
                    QualityEval.eval_date.between(start, end))
            .group_by(Drying.farm_id)
        ):
            rows[farm_id]["score_avg"] = round(float(score), 1) if score is not None else None
        for alert in alert_service.compute_alerts(db, farm_ids):
            rows[alert.farm_id][f"alerts_{alert.severity}"] += 1
        broca, roya, threshold = self._health(farm_ids, "farm")
        for (farm_id, _), value in broca.items():
            rows[farm_id]["broca_pct"] = value
            rows[farm_id]["broca_threshold"] = threshold.get((farm_id, rows[farm_id]["farm_name"]))
        for (farm_id, _), value in roya.items():
            rows[farm_id]["roya_pct"] = value
        for farm_id, total in (
            self._stored(farm_ids).with_entities(Drying.farm_id, func.sum(Drying.output_kg)).group_by(Drying.farm_id)
        ):
            rows[farm_id]["stored_kg"] = _float(total)
        return list(rows.values())
