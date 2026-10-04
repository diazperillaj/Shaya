"""
Validación automática del dataset generado (generador-sintetico-ml §3.7).

Dos tipos de chequeo:

- **Errores** (la generación falla): reglas que un dataset válido no puede
  romper — balance de masas, fechas encadenadas, rangos físicos, la
  trazabilidad que calcula la aplicación frente a la del mundo simulado, el
  % de faltantes y los valores recortados.
- **Advertencias**: masa insuficiente en alguna zona de una variable con
  umbral (§3.4). El dataset es válido, pero el modelo no podrá aprender esa
  parte de la curva.

Los chequeos de base de datos leen lo escrito; los estadísticos usan el
mundo simulado (la base no guarda lo no registrado ni las latentes).
"""

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.farm_operations.models import (
    CropCycle,
    Drying,
    DryingInput,
    Harvest,
    HarvestWork,
    Plot,
    QualityEval,
    WetProcessing,
    WetProcessingInput,
)
from app.farm_operations.models.enums import DryingStatusEnum, HarvestStatusEnum, WetProcessingStatusEnum
from app.farm_operations.services.cycle_records import CYCLE_LABORS
from app.farm_operations.services.dates import business_date
from app.farm_operations.services.traceability import drying_composition
from app.models.parchment import Parchment
from scripts.farm_ml import rules
from scripts.farm_ml.persist import Persisted
from scripts.farm_ml.world import World

ZERO = Decimal(0)
MIN_FLOWERING_TO_HARVEST_DAYS = 150


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    severity: str = "error"   # error | warning


@dataclass
class Report:
    checks: list = field(default_factory=list)

    def add(self, name: str, problems: list, detail_ok: str, severity: str = "error", limit: int = 5) -> None:
        if problems:
            shown = "; ".join(str(p) for p in problems[:limit])
            more = f" (y {len(problems) - limit} más)" if len(problems) > limit else ""
            self.checks.append(Check(name, False, f"{len(problems)} casos: {shown}{more}", severity))
        else:
            self.checks.append(Check(name, True, detail_ok, severity))

    @property
    def errors(self) -> list:
        return [c for c in self.checks if not c.ok and c.severity == "error"]

    @property
    def warnings(self) -> list:
        return [c for c in self.checks if not c.ok and c.severity == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "checks": [c.__dict__ for c in self.checks],
        }


def validate(db: Session, world: World, persisted: Persisted) -> Report:
    report = Report()
    farm_ids = [farm.id for farm in persisted.farms.values()]
    end = world.params.end_date
    check_mass_balance(db, report, farm_ids)
    check_dates(db, report, farm_ids, end)
    check_ranges(db, report, farm_ids)
    check_traceability(report, world, persisted)
    check_missing(report, world)
    check_clipping(report, world)
    check_correlation(report, world)
    check_zones(report, world)
    return report


# ── Balance de masas ──────────────────────────────────────────────────────


def check_mass_balance(db: Session, report: Report, farm_ids: list) -> None:
    harvests = (
        db.query(Harvest, func.coalesce(func.sum(WetProcessingInput.cherry_kg), 0))
        .join(CropCycle, Harvest.crop_cycle_id == CropCycle.id)
        .join(Plot, CropCycle.plot_id == Plot.id)
        .outerjoin(WetProcessingInput, WetProcessingInput.harvest_id == Harvest.id)
        .filter(Plot.farm_id.in_(farm_ids))
        .group_by(Harvest.id)
        .all()
    )
    report.add("Cosecha → beneficios: lo aportado no supera el total", [
        f"cosecha {h.id}: {used} > {h.total_cherry_kg}"
        for h, used in harvests
        if h.status == HarvestStatusEnum.closed and Decimal(used) > h.total_cherry_kg
    ], f"{len(harvests)} cosechas")

    wets = db.query(WetProcessing).filter(WetProcessing.farm_id.in_(farm_ids)).all()
    problems = []
    for wet in wets:
        cherry = sum((i.cherry_kg for i in wet.inputs), ZERO)
        if wet.washed_kg is not None and wet.washed_kg + (wet.floats_kg or ZERO) > cherry:
            problems.append(f"beneficio {wet.id}: flotes + lavado > cereza")
    report.add("Beneficio: cereza ≥ flotes + café lavado", problems, f"{len(wets)} beneficios")

    dried = dict(
        db.query(DryingInput.wet_processing_id, func.sum(DryingInput.wet_kg))
        .join(WetProcessing, DryingInput.wet_processing_id == WetProcessing.id)
        .filter(WetProcessing.farm_id.in_(farm_ids))
        .group_by(DryingInput.wet_processing_id)
        .all()
    )
    by_id = {wet.id: wet for wet in wets}
    report.add("Beneficio → secados: lo secado no supera el lavado (solo beneficios completados)", [
        f"beneficio {wet_id}"
        for wet_id, kg in dried.items()
        if by_id[wet_id].status != WetProcessingStatusEnum.completed or kg > by_id[wet_id].washed_kg
    ], f"{len(dried)} beneficios secados")

    dryings = db.query(Drying).filter(Drying.farm_id.in_(farm_ids)).all()
    report.add("Secado: pergamino seco ≤ café lavado que entró", [
        f"secado {d.id}"
        for d in dryings
        if d.output_kg is not None and d.output_kg > sum((i.wet_kg for i in d.inputs), ZERO)
    ], f"{len(dryings)} secados")


# ── Fechas encadenadas ────────────────────────────────────────────────────


def check_dates(db: Session, report: Report, farm_ids: list, end: date) -> None:
    cycles = (
        db.query(CropCycle).join(Plot, CropCycle.plot_id == Plot.id)
        .filter(Plot.farm_id.in_(farm_ids)).order_by(CropCycle.plot_id, CropCycle.cycle_number).all()
    )
    by_plot = defaultdict(list)
    for cycle in cycles:
        by_plot[cycle.plot_id].append(cycle)
    report.add("Ciclos de un lote sin solaparse, numerados en orden", [
        f"lote {plot_id}"
        for plot_id, items in by_plot.items()
        if any(a.end_date is None or b.start_date <= a.end_date for a, b in zip(items, items[1:]))
        or [c.cycle_number for c in items] != list(range(1, len(items) + 1))
    ], f"{len(cycles)} ciclos")

    ranges = {c.id: (c.start_date, c.end_date or end) for c in cycles}
    problems = []
    for name, (model, column) in CYCLE_LABORS.items():
        rows = db.query(model.crop_cycle_id, column).filter(model.crop_cycle_id.in_(list(ranges))).all()
        problems += [f"{name} del ciclo {cid}" for cid, day in rows if not ranges[cid][0] <= day <= ranges[cid][1]]
    report.add("Labores dentro de las fechas de su ciclo", problems, "todas las labores")

    harvests = db.query(Harvest).filter(Harvest.crop_cycle_id.in_(list(ranges))).all()
    flowering_model, flowering_column = CYCLE_LABORS["flowering-records"]
    flowerings: dict[int, list] = defaultdict(list)
    for cycle_id, day in (
        db.query(flowering_model.crop_cycle_id, flowering_column)
        .filter(flowering_model.crop_cycle_id.in_(list(ranges))).all()
    ):
        flowerings[cycle_id].append(day)
    problems = []
    for harvest in harvests:
        start, stop = ranges[harvest.crop_cycle_id]
        if not start <= harvest.start_date <= (harvest.end_date or end) <= stop:
            problems.append(f"cosecha {harvest.id} fuera del ciclo")
        # El fruto tarda ~32 semanas: ninguna cosecha llega a menos de 150 días de una floración.
        # Una floración posterior es de la temporada siguiente (p. ej., en un ciclo sin cerrar).
        if any(timedelta(0) <= harvest.start_date - day < timedelta(days=MIN_FLOWERING_TO_HARVEST_DAYS)
               for day in flowerings.get(harvest.crop_cycle_id, [])):
            problems.append(f"cosecha {harvest.id} a menos de {MIN_FLOWERING_TO_HARVEST_DAYS} días de una floración")
        for work in harvest.works:
            if not harvest.start_date <= work.work_date <= (harvest.end_date or end):
                problems.append(f"trabajo {work.id} fuera de su cosecha")
    report.add("Floración ≥ 150 días antes de cada cosecha; cosechas y recolección dentro de su ciclo",
               problems, f"{len(harvests)} cosechas")

    wets = db.query(WetProcessing).filter(WetProcessing.farm_id.in_(farm_ids)).all()
    problems = []
    for wet in wets:
        first_harvest = min(i.harvest.start_date for i in wet.inputs)
        if wet.pulped_at is not None and business_date(wet.pulped_at) < first_harvest:
            problems.append(f"beneficio {wet.id}: despulpado antes de la cosecha")
        if wet.pulped_at and wet.fermentation_start and wet.fermentation_start < wet.pulped_at:
            problems.append(f"beneficio {wet.id}: fermentación antes del despulpado")
    report.add("Cosecha < despulpado < fermentación", problems, f"{len(wets)} beneficios")

    dryings = db.query(Drying).filter(Drying.farm_id.in_(farm_ids)).all()
    problems = []
    for drying in dryings:
        for item in drying.inputs:
            wet = item.wet_processing
            if wet.fermentation_end is not None and drying.end_date is not None \
                    and business_date(wet.fermentation_end) > drying.end_date:
                problems.append(f"secado {drying.id}: termina antes de lavarse su café")
            if wet.pulped_at is not None and business_date(wet.pulped_at) > (drying.end_date or end):
                problems.append(f"secado {drying.id}: café despulpado después del secado")
        # Cada aporte se ancla en su primer evento registrado (o en su cosecha si no hay ninguno)
        anchors = []
        for item in drying.inputs:
            wet = item.wet_processing
            events = [m for m in (wet.pulped_at, wet.fermentation_start, wet.fermentation_end) if m is not None]
            anchors.append(business_date(min(events)) if events else min(i.harvest.start_date for i in wet.inputs))
        if drying.start_date < min(anchors):
            problems.append(f"secado {drying.id}: empieza antes de que exista su café")
        if drying.end_date is not None and any(c.check_date > drying.end_date for c in drying.humidity_checks):
            problems.append(f"secado {drying.id}: medición después del cierre")
        if drying.status == DryingStatusEnum.completed and drying.end_date < drying.start_date:
            problems.append(f"secado {drying.id}: fin antes del inicio")
    report.add("Beneficio < secado; mediciones dentro del secado", problems, f"{len(dryings)} secados")

    drying_ends = {d.id: d.end_date for d in dryings}
    evals = db.query(QualityEval).filter(QualityEval.drying_id.in_(list(drying_ends))).all()
    parchments = db.query(Parchment).filter(Parchment.drying_id.in_(list(drying_ends))).all()
    report.add("Secado < evaluación en pergamino e ingreso al inventario", [
        f"evaluación {e.id}" for e in evals if drying_ends[e.drying_id] is None or e.eval_date < drying_ends[e.drying_id]
    ] + [
        f"pergamino {p.id}" for p in parchments if p.purchase_date < drying_ends[p.drying_id]
    ], f"{len(evals)} evaluaciones, {len(parchments)} pergaminos")


# ── Rangos ────────────────────────────────────────────────────────────────


def check_ranges(db: Session, report: Report, farm_ids: list) -> None:
    columns = {"score": "score", "defects_pct": "defects_pct", "yield_factor": "yield_factor", "humidity_pct": "humidity_pct"}
    evals = (
        db.query(QualityEval).join(Drying, QualityEval.drying_id == Drying.id)
        .filter(Drying.farm_id.in_(farm_ids)).all()
    )
    problems = []
    for evaluation in evals:
        for target, column in columns.items():
            value = getattr(evaluation, column)
            low, high = rules.TARGET_RANGES[target]
            if value is None or not low <= value <= high:
                problems.append(f"evaluación {evaluation.id}: {column}={value}")
    report.add("Targets en pergamino completos y dentro de su rango físico", problems, f"{len(evals)} evaluaciones")

    dryings = db.query(Drying).filter(Drying.farm_id.in_(farm_ids), Drying.status == DryingStatusEnum.completed).all()
    report.add("Humedad final del secado verosímil (5–30 %)", [
        f"secado {d.id}: {d.final_humidity_pct}" for d in dryings if not 5 <= d.final_humidity_pct <= 30
    ], f"{len(dryings)} secados cerrados")

    per_person_day = (
        db.query(HarvestWork.employee_id, HarvestWork.work_date, func.sum(HarvestWork.kg_collected), func.count())
        .join(Harvest).join(CropCycle).join(Plot)
        .filter(Plot.farm_id.in_(farm_ids))
        .group_by(HarvestWork.employee_id, HarvestWork.work_date)
        .all()
    )
    report.add("Recolección diaria verosímil (≤ 250 kg y un solo lote por persona y día)", [
        f"empleado {employee} el {day}: {kg} kg en {n} registros"
        for employee, day, kg, n in per_person_day if n > 1 or (kg or 0) > 250
    ], f"{len(per_person_day)} jornadas de recolección")


# ── Trazabilidad: la aplicación frente al mundo ───────────────────────────


def check_traceability(report: Report, world: World, persisted: Persisted) -> None:
    """La composición que calcula la aplicación coincide con la cereza que el mundo trazó."""
    problems, compared = [], 0
    for farm in world.farms:
        for sim in farm.dryings:
            if not sim.audit:
                continue
            drying = persisted.dryings[sim.key]
            traced = float(drying_composition(drying)["cherry_kg_traced"])
            expected = sim.audit["x_cherry_kg_traced"]
            compared += 1
            if abs(traced - expected) > max(0.05, expected * 1e-4):
                problems.append(f"{sim.key}: aplicación {traced:.3f} kg, mundo {expected:.3f} kg")
    report.add("Trazabilidad de la aplicación = cereza trazada por el mundo", problems, f"{compared} secados cerrados")


# ── Estadísticos del mundo ────────────────────────────────────────────────


def check_missing(report: Report, world: World) -> None:
    """% de faltantes efectivo frente al configurado (con el hábito de registro de cada finca)."""
    level = world.params.missing_level
    groups: dict[str, list] = defaultdict(lambda: [0, 0, 0.0])
    for farm, group, recorded in world.registered():
        entry = groups[group]
        entry[0] += 1
        entry[1] += not recorded
        entry[2] += rules.missing_probability(level, group, farm.profile.registration)
    problems, details = [], []
    for group, (total, missing, expected) in sorted(groups.items()):
        effective, configured = missing / total, expected / total
        details.append(f"{group} {effective:.0%}/{configured:.0%}")
        if total >= 30 and abs(effective - configured) > rules.missing_tolerance(configured, total):
            problems.append(f"{group}: efectivo {effective:.0%}, configurado {configured:.0%} (n={total})")
    report.add("Faltantes efectivos ≈ configurados", problems, "efectivo/configurado: " + ", ".join(details))


def check_clipping(report: Report, world: World) -> None:
    audits = [d.audit for d in world.all_dryings() if d.audit]
    clipped = sum(any(v for k, v in a.items() if k.startswith("clipped_")) for a in audits)
    share = clipped / len(audits) if audits else 0.0
    problems = [f"{clipped} de {len(audits)} ({share:.2%})"] if share > rules.MAX_CLIP_SHARE else []
    report.add(f"Valores recortados por límites físicos < {rules.MAX_CLIP_SHARE:.1%}", problems,
               f"{clipped} de {len(audits)} secados")


def check_correlation(report: Report, world: World) -> None:
    """Altitud–temperatura media registrada: negativa fuerte, pero no perfecta."""
    pairs = []
    for farm in world.farms:
        temps = [(r.temp_min + r.temp_max) / 2 for r in farm.climate_records
                 if r.recorded and r.temp_min is not None and r.temp_max is not None]
        if len(temps) >= 30:
            pairs.append((farm.altitude, sum(temps) / len(temps)))
    if len(pairs) < 3:
        report.checks.append(Check("Correlación altitud–temperatura", True,
                                   "sin fincas suficientes con termómetro para medirla", "warning"))
        return
    r = pearson(pairs)
    low, high = rules.ALTITUDE_TEMPERATURE_CORRELATION
    problems = [] if low < r < high else [f"r = {r:.3f}, esperado entre {low} y {high}"]
    report.add("Correlación altitud–temperatura fuerte pero no perfecta", problems, f"r = {r:.3f} ({len(pairs)} fincas)")


def pearson(pairs: list[tuple[float, float]]) -> float:
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0


def zone_shares(world: World) -> dict:
    audits = [d.audit for d in world.all_dryings() if d.audit]
    shares = {}
    for zone in rules.ZONES:
        values = [a[f"x_{zone.variable}"] for a in audits]
        low, high = zone.cuts
        n = len(values) or 1
        shares[zone.variable] = (
            sum(v < low for v in values) / n,
            sum(low <= v <= high for v in values) / n,
            sum(v > high for v in values) / n,
        )
    return shares


def check_zones(report: Report, world: World) -> None:
    """Masa por zona en las variables con umbral (§3.4): advertencia si una zona queda corta."""
    for zone in rules.ZONES:
        shares = zone_shares(world)[zone.variable]
        problems = [
            f"«{label}» {share:.0%} < {minimum:.0%}"
            for label, share, minimum in zip(zone.labels, shares, zone.min_share)
            if share < minimum
        ]
        detail = ", ".join(f"{label} {share:.0%}" for label, share in zip(zone.labels, shares))
        report.add(f"Masa por zona: {zone.variable}", problems, detail, severity="warning")
