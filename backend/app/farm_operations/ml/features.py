"""
Features del modelo de calidad (generador-sintetico-ml §4).

Una sola extracción para el entrenamiento y la proyección. Cada fila parte
de un **origen ponderado**: qué ciclos, cosechas, beneficios y secados
aportan y con cuántos kg de cereza (la proporción de la trazabilidad). El
entrenamiento arma una fila por secado cerrado, a la fecha de su cierre
(`drying_origins`); la proyección, una por ciclo activo, a hoy
(`cycle_origins`). De ahí en adelante el cálculo es el mismo.

Reglas anti-fuga:
- Solo cuentan los datos con fecha ≤ la fecha de referencia de la fila.
- Lo previo a la cosecha se mide hasta el inicio de la primera pasada del
  ciclo: lo que pasa después ya no cambia ese grano.
- Las evaluaciones en pergamino son los targets: nunca se leen aquí.

Trabaja por lotes de ids (pocas consultas para miles de filas) y sin
pandas, para correr igual en la API que en el entrenamiento.
"""

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from statistics import median
from typing import Any, Iterable, Mapping, Optional

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.farm_operations.models import (
    ClimateRecord,
    CropCycle,
    CulturalPractice,
    Drying,
    Farm,
    Fertilization,
    FloweringRecord,
    Harvest,
    HarvestWork,
    PestMonitoring,
    PhytosanitaryApp,
    Plot,
    PlotEvent,
    QualityEval,
    SoilAnalysis,
    Supply,
    WetProcessing,
    WetProcessingInput,
)
from app.farm_operations.models.enums import (
    CulturalPracticeTypeEnum,
    DryingStatusEnum,
    IntensityEnum,
    PlotEventTypeEnum,
    QualityStageEnum,
    WetProcessingStatusEnum,
)
from app.farm_operations.services.dates import BUSINESS_TZ
from app.farm_operations.services.traceability import traced_cherry_select

FILLING_DAYS = 120   # llenado del grano: los 120 días previos al inicio de la cosecha
DELIVERY_HOUR = 16   # la cereza de un día de recolección llega al beneficiadero a las 16:00
CHUNK = 5000         # ids por consulta
ONE_DAY = timedelta(days=1)


@dataclass(frozen=True)
class Feature:
    name: str
    stage: str        # cuándo existe el dato: pre (antes de cosechar), harvest, wet (beneficio), drying
    group: str        # grupo para la completitud
    label: str
    categorical: bool = False


FEATURES: tuple[Feature, ...] = (
    Feature("variety", "pre", "lote", "Variedad", categorical=True),
    Feature("altitude", "pre", "lote", "Altitud (m)"),
    Feature("effective_age_years", "pre", "lote", "Edad efectiva (años)"),
    Feature("shade_type", "pre", "lote", "Sombra", categorical=True),
    Feature("soil_type", "pre", "lote", "Tipo de suelo", categorical=True),
    Feature("density_trees_ha", "pre", "lote", "Densidad (árboles/ha)"),
    Feature("soil_ph", "pre", "suelo", "pH del suelo"),
    Feature("soil_om_pct", "pre", "suelo", "Materia orgánica (%)"),
    Feature("rain_mm_filling", "pre", "clima", "Lluvia en el llenado del grano (mm)"),
    Feature("temp_avg_cycle", "pre", "clima", "Temperatura media del ciclo (°C)"),
    Feature("n_fertilizations", "pre", "nutricion", "Fertilizaciones"),
    Feature("n_kg_ha", "pre", "nutricion", "Nitrógeno aplicado (kg/ha)"),
    Feature("days_since_last_fert", "pre", "nutricion", "Días desde la última fertilización"),
    Feature("n_phyto_apps", "pre", "sanidad", "Aplicaciones fitosanitarias"),
    Feature("broca_pct_last", "pre", "sanidad", "Broca en campo, último muestreo (%)"),
    Feature("roya_pct_max", "pre", "sanidad", "Roya, máximo en el llenado (%)"),
    Feature("n_weedings", "pre", "practicas", "Deshierbas"),
    Feature("n_prunings", "pre", "practicas", "Podas"),
    Feature("days_flowering_to_harvest", "harvest", "cosecha", "Días de la floración a la cosecha"),
    Feature("pass_number", "harvest", "cosecha", "Pasada"),
    Feature("cherry_kg", "harvest", "cosecha", "Cereza de la pasada (kg)"),
    Feature("ripe_pct", "harvest", "calidad_cereza", "Maduros (%)"),
    Feature("green_pct", "harvest", "calidad_cereza", "Verdes (%)"),
    Feature("bored_pct", "harvest", "calidad_cereza", "Brocados (%)"),
    Feature("floats_pct", "wet", "beneficio", "Flotes (%)"),
    Feature("hours_harvest_to_pulp", "wet", "beneficio", "Horas de la recolección al despulpado"),
    Feature("fermentation_hours", "wet", "beneficio", "Horas de fermentación"),
    Feature("fermentation_temp_c", "wet", "beneficio", "Temperatura de la fermentación (°C)"),
    Feature("process_day_temp_c", "wet", "beneficio", "Temperatura del día del beneficio (°C)"),
    Feature("fermentation_method", "wet", "beneficio", "Método de fermentación", categorical=True),
    Feature("drying_method", "drying", "secado", "Método de secado", categorical=True),
    Feature("drying_days", "drying", "secado", "Días de secado"),
    Feature("rain_mm_drying", "drying", "secado", "Lluvia durante el secado (mm)"),
    Feature("final_humidity_pct", "drying", "secado", "Humedad final del secado (%)"),
)
FEATURE_NAMES: tuple[str, ...] = tuple(f.name for f in FEATURES)
CATEGORICAL_MASK = np.array([f.categorical for f in FEATURES])
GROUPS: tuple[str, ...] = tuple(dict.fromkeys(f.group for f in FEATURES))
STAGES = ("pre", "harvest", "wet", "drying")

# Fracción de nitrógeno: «N 46 %», «Nitrógeno 46 %» o el grado «17-6-18» (N primero)
_N_PERCENT = re.compile(r"\bN\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*%")
_N_WORD = re.compile(r"nitr[oó]geno\D{0,20}(\d+(?:[.,]\d+)?)\s*%", re.IGNORECASE)
_GRADE = re.compile(r"(?<![\d.,])(\d{1,2}(?:[.,]\d+)?)-\d{1,2}(?:[.,]\d+)?-\d{1,2}(?:[.,]\d+)?")
_ANY_PERCENT = re.compile(r"\d\s*%")
# Unidades del insumo a kg (los líquidos, a densidad 1)
UNIT_KG = {"kg": 1.0, "kilo": 1.0, "kilos": 1.0, "g": 0.001, "gr": 0.001, "l": 1.0, "lt": 1.0,
           "litro": 1.0, "litros": 1.0, "cc": 0.001, "ml": 0.001, "bulto": 50.0, "bultos": 50.0}
INTENSITY_RANK = {IntensityEnum.high: 0, IntensityEnum.medium: 1, IntensityEnum.low: 2}


def nitrogen_fraction(composition: Optional[str], name: Optional[str] = None) -> Optional[float]:
    """
    Fracción de N de un insumo según su composición (o su nombre). Una
    composición declarada sin nitrógeno (p. ej. «K 60 %») vale 0; sin
    composición reconocible, no se sabe.
    """
    for text in (composition, name):
        if not text:
            continue
        match = _N_PERCENT.search(text) or _N_WORD.search(text) or _GRADE.search(text)
        if match:
            return float(match.group(1).replace(",", ".")) / 100.0
    if composition and _ANY_PERCENT.search(composition):
        return 0.0
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Orígenes: qué aporta a cada fila y con cuántos kg de cereza
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Origin:
    key: int                 # id del secado (entrenamiento) o del ciclo (proyección)
    farm_id: int
    as_of: date
    cycles: dict[int, float] = field(default_factory=dict)
    harvests: dict[int, float] = field(default_factory=dict)
    wets: dict[int, float] = field(default_factory=dict)
    dryings: dict[int, float] = field(default_factory=dict)


@dataclass
class FeatureRow:
    key: int
    farm_id: int
    as_of: date
    values: dict[str, Any]
    stages: frozenset[str]   # etapas que ya ocurrieron

    @property
    def completeness(self) -> float:
        """Fracción de grupos de features con al menos un dato."""
        present = {f.group for f in FEATURES if is_present(self.values.get(f.name))}
        return len(present) / len(GROUPS)


def _chunks(ids: Iterable[int]):
    ids = sorted(set(ids))
    for start in range(0, len(ids), CHUNK):
        yield ids[start:start + CHUNK]


def _add(weights: dict[int, float], key: int, kg) -> None:
    weights[key] = weights.get(key, 0.0) + float(kg)


def drying_origins(db: Session, drying_ids: Iterable[int]) -> list[Origin]:
    """Una fila por secado cerrado, a la fecha de su cierre, con la cereza trazada de cada origen."""
    origins: dict[int, Origin] = {}
    traced = traced_cherry_select().subquery()
    for chunk in _chunks(drying_ids):
        for drying_id, farm_id, end in (
            db.query(Drying.id, Drying.farm_id, Drying.end_date)
            .filter(Drying.id.in_(chunk), Drying.end_date.isnot(None))
        ):
            origins[drying_id] = Origin(drying_id, farm_id, end, dryings={drying_id: 1.0})
        for drying_id, wet_id, harvest_id, cycle_id, kg in (
            db.query(traced.c.drying_id, traced.c.wet_processing_id, traced.c.harvest_id,
                     traced.c.crop_cycle_id, traced.c.cherry_kg)
            .filter(traced.c.drying_id.in_(chunk))
        ):
            origin = origins.get(drying_id)
            if origin is not None:
                _add(origin.harvests, harvest_id, kg)
                _add(origin.wets, wet_id, kg)
                _add(origin.cycles, cycle_id, kg)
    return [origins[key] for key in sorted(origins)]


def cycle_origins(db: Session, cycle_ids: Iterable[int], as_of: date) -> list[Origin]:
    """
    Una fila por ciclo, a `as_of`: el ciclo y lo que ya pasó con su café
    (pasadas iniciadas, beneficios terminados y secados cerrados, con su
    cereza). Un beneficio que aún fermenta o un secado abierto todavía no
    cuentan: sus datos están a medias y la etapa se rellena como futura.
    """
    origins: dict[int, Origin] = {}
    traced = traced_cherry_select().subquery()
    picked = (
        db.query(HarvestWork.harvest_id.label("harvest_id"), func.sum(HarvestWork.kg_collected).label("kg"))
        .group_by(HarvestWork.harvest_id).subquery()
    )
    for chunk in _chunks(cycle_ids):
        for cycle_id, farm_id in (
            db.query(CropCycle.id, Plot.farm_id).join(Plot, CropCycle.plot_id == Plot.id).filter(CropCycle.id.in_(chunk))
        ):
            origins[cycle_id] = Origin(cycle_id, farm_id, as_of, cycles={cycle_id: 1.0})
        for harvest_id, cycle_id, total, kg in (
            db.query(Harvest.id, Harvest.crop_cycle_id, Harvest.total_cherry_kg, picked.c.kg)
            .outerjoin(picked, picked.c.harvest_id == Harvest.id)
            .filter(Harvest.crop_cycle_id.in_(chunk), Harvest.start_date <= as_of)
        ):
            weight = total if total else kg if kg else 1.0   # una pasada abierta pesa lo recogido
            _add(origins[cycle_id].harvests, harvest_id, weight)
        for wet_id, cycle_id, kg in (
            db.query(WetProcessingInput.wet_processing_id, Harvest.crop_cycle_id, func.sum(WetProcessingInput.cherry_kg))
            .join(Harvest, WetProcessingInput.harvest_id == Harvest.id)
            .join(WetProcessing, WetProcessingInput.wet_processing_id == WetProcessing.id)
            .filter(Harvest.crop_cycle_id.in_(chunk), Harvest.start_date <= as_of,
                    WetProcessing.status == WetProcessingStatusEnum.completed)
            .group_by(WetProcessingInput.wet_processing_id, Harvest.crop_cycle_id)
        ):
            _add(origins[cycle_id].wets, wet_id, kg)
        for drying_id, cycle_id, kg in (
            db.query(traced.c.drying_id, traced.c.crop_cycle_id, func.sum(traced.c.cherry_kg))
            .join(Drying, Drying.id == traced.c.drying_id)
            .filter(traced.c.crop_cycle_id.in_(chunk), Drying.status == DryingStatusEnum.completed,
                    Drying.end_date <= as_of)
            .group_by(traced.c.drying_id, traced.c.crop_cycle_id)
        ):
            _add(origins[cycle_id].dryings, drying_id, kg)
    return [origins[key] for key in sorted(origins)]


# ═══════════════════════════════════════════════════════════════════════════
# Datos de apoyo: se cargan una vez por lote de filas
# ═══════════════════════════════════════════════════════════════════════════


def _float(value) -> Optional[float]:
    return float(value) if value is not None else None


def is_present(value) -> bool:
    return value is not None and not (isinstance(value, float) and math.isnan(value))


def _wmean(pairs: Iterable[tuple[Optional[float], float]]) -> Optional[float]:
    total = weight = 0.0
    for value, w in pairs:
        if is_present(value) and w > 0:
            total += value * w
            weight += w
    return total / weight if weight else None


def _dominant(pairs: Iterable[tuple[Optional[str], float]]) -> Optional[str]:
    """La categoría con más peso (en empate, la primera en orden alfabético)."""
    totals: dict[str, float] = defaultdict(float)
    for value, w in pairs:
        if is_present(value):
            totals[value] += w
    return max(sorted(totals), key=totals.get) if totals else None


@dataclass
class _Cycle:
    id: int
    start: date
    plot_id: int
    farm_id: int
    variety: str
    shade_type: Optional[str]
    soil_type: Optional[str]
    area: Optional[float]
    density: Optional[float]
    planting: Optional[date]
    altitude: Optional[float]


class _Climate:
    """Clima diario de cada finca; el registro de un lote, si existe, manda sobre el de la finca."""

    def __init__(self, rows):
        self.rain: dict[tuple, dict[date, float]] = defaultdict(dict)
        self.temp: dict[tuple, dict[date, float]] = defaultdict(dict)
        for farm_id, plot_id, day, rain, low, high in rows:
            if rain is not None:
                self.rain[(farm_id, plot_id)][day] = float(rain)
            if low is not None and high is not None:
                self.temp[(farm_id, plot_id)][day] = (float(low) + float(high)) / 2.0

    @staticmethod
    def _values(table, farm_id: int, plot_id: Optional[int], start: date, end: date) -> list[float]:
        farm = table.get((farm_id, None), {})
        plot = table.get((farm_id, plot_id), {}) if plot_id is not None else {}
        values, day = [], start
        while day <= end:
            value = plot.get(day, farm.get(day))
            if value is not None:
                values.append(value)
            day += ONE_DAY
        return values

    def rain_total(self, farm_id: int, plot_id: Optional[int], start: date, end: date) -> Optional[float]:
        """Lluvia del rango: el promedio de los días registrados por los días del rango."""
        values = self._values(self.rain, farm_id, plot_id, start, end)
        return sum(values) / len(values) * ((end - start).days + 1) if values else None

    def temp_mean(self, farm_id: int, plot_id: Optional[int], start: date, end: date) -> Optional[float]:
        values = self._values(self.temp, farm_id, plot_id, start, end)
        return sum(values) / len(values) if values else None


class _Data:
    """Todo lo que necesitan las filas de un lote de orígenes, en unas pocas consultas."""

    def __init__(self, db: Session, origins: list[Origin]):
        self.db = db
        cycle_ids = {c for o in origins for c in o.cycles}
        harvest_ids = {h for o in origins for h in o.harvests}
        wet_ids = {w for o in origins for w in o.wets}
        drying_ids = {d for o in origins for d in o.dryings}
        self._cache: dict[tuple, dict] = {}

        self.cycles: dict[int, _Cycle] = {}
        for chunk in _chunks(cycle_ids):
            for row in (
                db.query(CropCycle.id, CropCycle.start_date, Plot.id, Plot.farm_id, Plot.variety, Plot.shade_type,
                         Plot.soil_type, Plot.area, Plot.row_spacing_m, Plot.plant_spacing_m, Plot.planting_date,
                         Plot.initial_age_years, Plot.created_at, Farm.altitude)
                .join(Plot, CropCycle.plot_id == Plot.id).join(Farm, Plot.farm_id == Farm.id)
                .filter(CropCycle.id.in_(chunk))
            ):
                (cycle_id, start, plot_id, farm_id, variety, shade, soil, area, row_m, plant_m,
                 planting, initial_age, created, altitude) = row
                if planting is None and initial_age is not None:
                    # Sin fecha de siembra: la edad que tenía al registrarse el lote
                    planting = created.astimezone(BUSINESS_TZ).date() - timedelta(days=float(initial_age) * 365.25)
                density = 10000.0 / (float(row_m) * float(plant_m)) if row_m and plant_m else None
                self.cycles[cycle_id] = _Cycle(cycle_id, start, plot_id, farm_id, variety, shade, soil,
                                               _float(area), density, planting, _float(altitude))
        plot_ids = {c.plot_id for c in self.cycles.values()}
        farm_ids = {c.farm_id for c in self.cycles.values()} | {o.farm_id for o in origins}

        self.first_harvest: dict[int, date] = {}
        self.zocas: dict[int, list[date]] = defaultdict(list)
        self.soil: dict[int, list[tuple]] = defaultdict(list)
        self.ferts: dict[int, list[tuple]] = defaultdict(list)
        self.phyto: dict[int, list[date]] = defaultdict(list)
        self.monitorings: dict[int, list[tuple]] = defaultdict(list)
        self.practices: dict[int, list[tuple]] = defaultdict(list)
        self.flowerings: dict[int, list[tuple]] = defaultdict(list)
        for chunk in _chunks(cycle_ids):
            self.first_harvest.update(
                db.query(Harvest.crop_cycle_id, func.min(Harvest.start_date))
                .filter(Harvest.crop_cycle_id.in_(chunk)).group_by(Harvest.crop_cycle_id).all()
            )
            for cycle_id, day, quantity, unit, composition, name in (
                db.query(Fertilization.crop_cycle_id, Fertilization.application_date, Fertilization.quantity,
                         Supply.unit, Supply.composition, Supply.name)
                .join(Supply, Fertilization.supply_id == Supply.id).filter(Fertilization.crop_cycle_id.in_(chunk))
            ):
                factor = UNIT_KG.get((unit or "").strip().lower())
                fraction = nitrogen_fraction(composition, name)
                nitrogen = float(quantity) * factor * fraction if factor is not None and fraction is not None else None
                self.ferts[cycle_id].append((day, nitrogen))
            for cycle_id, day in (
                db.query(PhytosanitaryApp.crop_cycle_id, PhytosanitaryApp.application_date)
                .filter(PhytosanitaryApp.crop_cycle_id.in_(chunk))
            ):
                self.phyto[cycle_id].append(day)
            for cycle_id, day, broca, roya in (
                db.query(PestMonitoring.crop_cycle_id, PestMonitoring.monitoring_date, PestMonitoring.broca_pct,
                         PestMonitoring.roya_pct)
                .filter(PestMonitoring.crop_cycle_id.in_(chunk))
            ):
                self.monitorings[cycle_id].append((day, _float(broca), _float(roya)))
            for cycle_id, day, kind in (
                db.query(CulturalPractice.crop_cycle_id, CulturalPractice.practice_date, CulturalPractice.practice_type)
                .filter(CulturalPractice.crop_cycle_id.in_(chunk))
            ):
                self.practices[cycle_id].append((day, kind))
            for cycle_id, day, intensity in (
                db.query(FloweringRecord.crop_cycle_id, FloweringRecord.flowering_date, FloweringRecord.intensity)
                .filter(FloweringRecord.crop_cycle_id.in_(chunk))
            ):
                self.flowerings[cycle_id].append((day, intensity))
        for chunk in _chunks(plot_ids):
            for plot_id, day in (
                db.query(PlotEvent.plot_id, PlotEvent.event_date)
                .filter(PlotEvent.plot_id.in_(chunk), PlotEvent.event_type == PlotEventTypeEnum.zoca)
            ):
                self.zocas[plot_id].append(day)
            for plot_id, day, ph, organic in (
                db.query(SoilAnalysis.plot_id, SoilAnalysis.analysis_date, SoilAnalysis.ph, SoilAnalysis.organic_matter_pct)
                .filter(SoilAnalysis.plot_id.in_(chunk)).order_by(SoilAnalysis.analysis_date, SoilAnalysis.id)
            ):
                self.soil[plot_id].append((day, _float(ph), _float(organic)))

        self.harvests: dict[int, tuple] = {}
        self.cherry_evals: dict[int, list[tuple]] = defaultdict(list)
        for chunk in _chunks(harvest_ids):
            for harvest_id, cycle_id, number, start, total in (
                db.query(Harvest.id, Harvest.crop_cycle_id, Harvest.pass_number, Harvest.start_date, Harvest.total_cherry_kg)
                .filter(Harvest.id.in_(chunk))
            ):
                self.harvests[harvest_id] = (cycle_id, number, start, _float(total))
            for harvest_id, day, ripe, green, bored in (
                db.query(QualityEval.harvest_id, QualityEval.eval_date, QualityEval.ripe_pct, QualityEval.green_pct,
                         QualityEval.bored_pct)
                .filter(QualityEval.harvest_id.in_(chunk), QualityEval.stage == QualityStageEnum.cherry)
                .order_by(QualityEval.eval_date, QualityEval.id)
            ):
                self.cherry_evals[harvest_id].append((day, _float(ripe), _float(green), _float(bored)))

        self.wets: dict[int, tuple] = {}
        self.wet_cherry: dict[int, float] = {}
        wet_harvests: dict[int, set[int]] = defaultdict(set)
        for chunk in _chunks(wet_ids):
            for row in (
                db.query(WetProcessing.id, WetProcessing.farm_id, WetProcessing.floats_kg, WetProcessing.pulped_at,
                         WetProcessing.fermentation_start, WetProcessing.fermentation_end,
                         WetProcessing.fermentation_method, WetProcessing.ambient_temp_c)
                .filter(WetProcessing.id.in_(chunk))
            ):
                self.wets[row[0]] = row[1:]
            for wet_id, harvest_id, kg in (
                db.query(WetProcessingInput.wet_processing_id, WetProcessingInput.harvest_id, WetProcessingInput.cherry_kg)
                .filter(WetProcessingInput.wet_processing_id.in_(chunk))
            ):
                self.wet_cherry[wet_id] = self.wet_cherry.get(wet_id, 0.0) + float(kg)
                wet_harvests[wet_id].add(harvest_id)
        work_days: dict[int, set[date]] = defaultdict(set)
        for chunk in _chunks({h for hs in wet_harvests.values() for h in hs}):
            for harvest_id, day in (
                db.query(HarvestWork.harvest_id, HarvestWork.work_date).filter(HarvestWork.harvest_id.in_(chunk)).distinct()
            ):
                work_days[harvest_id].add(day)
        self.wet_days = {wet_id: sorted(set().union(*(work_days[h] for h in harvests)))
                         for wet_id, harvests in wet_harvests.items()}

        self.dryings: dict[int, tuple] = {}
        for chunk in _chunks(drying_ids):
            for row in (
                db.query(Drying.id, Drying.farm_id, Drying.method, Drying.status, Drying.start_date, Drying.end_date,
                         Drying.final_humidity_pct)
                .filter(Drying.id.in_(chunk))
            ):
                self.dryings[row[0]] = row[1:]
        farm_ids |= {d[0] for d in self.dryings.values()} | {w[0] for w in self.wets.values()}

        starts = [c.start for c in self.cycles.values()] + [o.as_of - timedelta(days=FILLING_DAYS) for o in origins]
        starts += [d[3] for d in self.dryings.values()]
        rows = []
        if origins and farm_ids:
            low, high = min(starts), max(o.as_of for o in origins)
            for chunk in _chunks(farm_ids):
                rows += (
                    db.query(ClimateRecord.farm_id, ClimateRecord.plot_id, ClimateRecord.record_date,
                             ClimateRecord.rainfall_mm, ClimateRecord.temp_min_c, ClimateRecord.temp_max_c)
                    .filter(ClimateRecord.farm_id.in_(chunk), ClimateRecord.record_date.between(low, high))
                    .order_by(ClimateRecord.record_date, ClimateRecord.id).all()
                )
        self.climate = _Climate(rows)

    # ── Por ciclo, a su fecha de referencia ───────────────────────────────

    def reference(self, cycle_id: int, as_of: date) -> date:
        """Inicio de la primera pasada (lo previo a la cosecha) o `as_of` si aún no se cosecha."""
        first = self.first_harvest.get(cycle_id)
        return min(first, as_of) if first is not None else as_of

    def cycle_values(self, cycle_id: int, as_of: date) -> dict:
        ref = self.reference(cycle_id, as_of)
        key = (cycle_id, ref)
        if key not in self._cache:
            self._cache[key] = self._cycle_values(self.cycles[cycle_id], ref)
        return self._cache[key]

    def _cycle_values(self, c: _Cycle, ref: date) -> dict:
        age = None
        if c.planting is not None:
            restart = max([c.planting] + [z for z in self.zocas.get(c.plot_id, []) if z <= ref])
            age = max((ref - restart).days, 0) / 365.25
        ph = organic = None
        for day, value_ph, value_om in self.soil.get(c.plot_id, []):
            if day <= ref:
                ph = value_ph if value_ph is not None else ph
                organic = value_om if value_om is not None else organic
        ferts = [(day, n) for day, n in self.ferts.get(c.id, []) if day <= ref]
        nitrogen = None
        if not ferts:
            nitrogen = 0.0
        elif c.area and all(n is not None for _, n in ferts):
            nitrogen = sum(n for _, n in ferts) / c.area
        monitorings = [m for m in self.monitorings.get(c.id, []) if m[0] <= ref]
        broca = [(day, value) for day, value, _ in monitorings if value is not None]
        filling_start = ref - timedelta(days=FILLING_DAYS)
        roya = [value for day, _, value in monitorings if value is not None and day >= filling_start]
        practices = [kind for day, kind in self.practices.get(c.id, []) if day <= ref]
        return {
            "variety": c.variety,
            "altitude": c.altitude,
            "effective_age_years": age,
            "shade_type": c.shade_type,
            "soil_type": c.soil_type,
            "density_trees_ha": c.density,
            "soil_ph": ph,
            "soil_om_pct": organic,
            "rain_mm_filling": self.climate.rain_total(c.farm_id, c.plot_id, filling_start, ref),
            "temp_avg_cycle": self.climate.temp_mean(c.farm_id, c.plot_id, c.start, ref),
            "n_fertilizations": float(len(ferts)),
            "n_kg_ha": nitrogen,
            "days_since_last_fert": float((ref - max(day for day, _ in ferts)).days) if ferts else None,
            "n_phyto_apps": float(sum(1 for day in self.phyto.get(c.id, []) if day <= ref)),
            "broca_pct_last": max(broca)[1] if broca else None,
            "roya_pct_max": max(roya) if roya else None,
            "n_weedings": float(sum(1 for k in practices if k == CulturalPracticeTypeEnum.weeding)),
            "n_prunings": float(sum(1 for k in practices if k == CulturalPracticeTypeEnum.pruning)),
        }

    # ── Por cosecha, beneficio y secado ───────────────────────────────────

    def main_flowering(self, cycle_id: int, before: date) -> Optional[date]:
        """La floración de mayor intensidad (y, entre iguales, la primera) previa a la pasada."""
        candidates = [(INTENSITY_RANK[i], day) for day, i in self.flowerings.get(cycle_id, []) if day < before]
        return min(candidates)[1] if candidates else None

    def harvest_values(self, harvest_id: int, as_of: date) -> dict:
        cycle_id, number, start, total = self.harvests[harvest_id]
        flowering = self.main_flowering(cycle_id, start)
        evals = [e for e in self.cherry_evals.get(harvest_id, []) if e[0] <= as_of]
        _, ripe, green, bored = evals[-1] if evals else (None, None, None, None)
        return {
            "days_flowering_to_harvest": float((start - flowering).days) if flowering else None,
            "pass_number": float(number),
            "cherry_kg": total,
            "ripe_pct": ripe,
            "green_pct": green,
            "bored_pct": bored,
        }

    def arrival(self, wet_id: int, pulped: datetime) -> Optional[datetime]:
        """La entrega de las 16:00 del último día de recolección anterior al despulpado."""
        arrival = None
        for day in self.wet_days.get(wet_id, []):
            moment = datetime.combine(day, time(DELIVERY_HOUR), BUSINESS_TZ)
            if moment <= pulped:
                arrival = moment
        return arrival

    def wet_values(self, wet_id: int) -> dict:
        farm_id, floats, pulped, start, end, method, ambient = self.wets[wet_id]
        cherry = self.wet_cherry.get(wet_id)
        arrival = self.arrival(wet_id, pulped) if pulped is not None else None
        day = arrival.date() if arrival else pulped.astimezone(BUSINESS_TZ).date() if pulped else None
        return {
            "floats_pct": float(floats) * 100.0 / cherry if floats is not None and cherry else None,
            "hours_harvest_to_pulp": (pulped - arrival).total_seconds() / 3600.0 if arrival else None,
            "fermentation_hours": (end - start).total_seconds() / 3600.0 if start and end else None,
            "fermentation_temp_c": _float(ambient),
            "process_day_temp_c": self.climate.temp_mean(farm_id, None, day, day) if day else None,
            "fermentation_method": method.value if method else None,
        }

    def drying_values(self, drying_id: int, as_of: date) -> dict:
        farm_id, method, status, start, end, humidity = self.dryings[drying_id]
        closed = status == DryingStatusEnum.completed and end is not None and end <= as_of
        return {
            "drying_method": method.value if method else None,
            "drying_days": float((end - start).days) if closed else None,
            "rain_mm_drying": self.climate.rain_total(farm_id, None, start, end) if closed else None,
            "final_humidity_pct": _float(humidity) if closed else None,
        }

    # ── La fila ───────────────────────────────────────────────────────────

    def row(self, o: Origin) -> FeatureRow:
        parts = {
            "pre": [(self.cycle_values(c, o.as_of), w) for c, w in o.cycles.items() if c in self.cycles],
            "harvest": [(self.harvest_values(h, o.as_of), w) for h, w in o.harvests.items() if h in self.harvests],
            "wet": [(self.wet_values(x), w) for x, w in o.wets.items() if x in self.wets],
            "drying": [(self.drying_values(d, o.as_of), w) for d, w in o.dryings.items() if d in self.dryings],
        }
        values = {}
        for f in FEATURES:
            pairs = [(part.get(f.name), w) for part, w in parts[f.stage]]
            values[f.name] = _dominant(pairs) if f.categorical else _wmean(pairs)
        stages = frozenset(stage for stage, items in parts.items() if items) | {"pre"}
        return FeatureRow(o.key, o.farm_id, o.as_of, values, stages)


def build_features(db: Session, origins: list[Origin]) -> list[FeatureRow]:
    """El vector de cada origen, en su mismo orden."""
    if not origins:
        return []
    data = _Data(db, origins)
    return [data.row(origin) for origin in origins]


# ═══════════════════════════════════════════════════════════════════════════
# Matriz para el modelo y relleno de las etapas que aún no ocurren
# ═══════════════════════════════════════════════════════════════════════════


def vocabularies(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    """Categorías vistas en el entrenamiento, por feature categórica."""
    seen: dict[str, set] = {f.name: set() for f in FEATURES if f.categorical}
    for row in rows:
        for name, values in seen.items():
            value = row.get(name)
            if is_present(value):
                values.add(str(value))
    return {name: sorted(values) for name, values in seen.items()}


def to_matrix(rows: Iterable[Mapping[str, Any]], vocab: Mapping[str, list[str]]) -> np.ndarray:
    """
    Matriz en el orden de `FEATURES`. Las categóricas van como su posición en
    el vocabulario; una categoría que el modelo no conoce queda como faltante.
    """
    rows = list(rows)
    index = {name: {value: i for i, value in enumerate(values)} for name, values in vocab.items()}
    matrix = np.full((len(rows), len(FEATURES)), np.nan)
    for i, row in enumerate(rows):
        for j, f in enumerate(FEATURES):
            value = row.get(f.name)
            if not is_present(value):
                continue
            if f.categorical:
                code = index.get(f.name, {}).get(str(value))
                if code is not None:
                    matrix[i, j] = code
            else:
                matrix[i, j] = float(value)
    return matrix


def reference_values(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Mediana (numéricas) o moda (categóricas) de cada feature entre las filas dadas."""
    columns: dict[str, list] = {f.name: [] for f in FEATURES}
    for row in rows:
        for name, values in columns.items():
            value = row.get(name)
            if is_present(value):
                values.append(value)
    result = {}
    for f in FEATURES:
        values = columns[f.name]
        if not values:
            continue
        if f.categorical:
            counts: dict[str, int] = defaultdict(int)
            for value in values:
                counts[str(value)] += 1
            result[f.name] = max(sorted(counts), key=counts.get)
        else:
            result[f.name] = float(median(values))
    return result


def fill_future_stages(values: Mapping[str, Any], stages: Iterable[str],
                       *references: Mapping[str, Any]) -> dict[str, Any]:
    """
    Proyección de un ciclo activo: las features de las etapas que aún no
    ocurren toman el valor típico de la finca (o, sin historia, el global).
    Lo que ya ocurrió y no se registró queda como faltante.
    """
    stages = set(stages)
    filled = dict(values)
    for f in FEATURES:
        if f.stage in stages:
            continue
        filled[f.name] = None
        for reference in references:
            if is_present(reference.get(f.name)):
                filled[f.name] = reference[f.name]
                break
    return filled
