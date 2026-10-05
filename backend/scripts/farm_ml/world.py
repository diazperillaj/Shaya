"""
Simulación del mundo cafetero sintético (generador-sintetico-ml §3.2).

Es pura y determinista: no toca la base de datos y, con los mismos
parámetros, produce exactamente el mismo mundo. Cada finca usa sus propios
generadores aleatorios, derivados de la semilla, para que cambiar una finca
no altere las demás.

El mundo distingue lo que **ocurre** de lo que **se registra**:

- Lo que ocurre (clima, broca, labores hechas, cosechas, beneficio, secado,
  calidad verdadera) sale de los generadores del mundo.
- Lo que se registra pasa además por el filtro de faltantes, que usa su
  propio generador. Así, `--missing-level none` y `realistic` simulan el
  mismo mundo y solo difieren en lo anotado (§3.6, §7.6).
"""

import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional

from app.farm_operations.services.dates import BUSINESS_TZ
from scripts.farm_ml import catalogs, rules
from scripts.farm_ml.rules import DRYING_METHODS, MANAGEMENT, SHADE_LEVELS, VARIETIES

# ═══════════════════════════════════════════════════════════════════════════
# Parámetros
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Params:
    end_date: date
    farms: int = 12
    plots_per_farm: tuple[int, int] = (2, 6)
    years: int = 5
    seed: int = 42
    missing_level: str = "realistic"
    inventory_available: bool = True

    @property
    def window_start(self) -> date:
        try:
            return self.end_date.replace(year=self.end_date.year - self.years)
        except ValueError:  # 29 de febrero
            return self.end_date.replace(year=self.end_date.year - self.years, day=28)

    @property
    def sim_start(self) -> date:
        """El clima y la sanidad arrancan antes, para que el primer ciclo tenga historia."""
        return self.window_start - timedelta(days=300)


# ═══════════════════════════════════════════════════════════════════════════
# Entidades del mundo
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class DayClimate:
    t_mean: float
    t_min: float
    t_max: float
    rain: float


@dataclass
class Registered:
    """Un registro candidato: ocurrió; `recorded` dice si el caficultor lo anotó."""

    group: str
    recorded: bool
    forced: bool = False   # lo dejó sin registrar una situación del presente, no el % de faltantes


@dataclass
class ClimateRec(Registered):
    day: date = None
    rainfall_mm: float = 0.0
    temp_min: Optional[float] = None
    temp_max: Optional[float] = None
    observations: Optional[str] = None


@dataclass
class EmployeeSim:
    key: str
    full_name: str
    active: bool = True
    last_work: Optional[date] = None


@dataclass
class EventSim:
    event_type: str
    day: date
    description: str


@dataclass
class SoilSim(Registered):
    day: date = None
    fields: dict = field(default_factory=dict)


@dataclass
class LaborSim(Registered):
    kind: str = ""        # fertilization, phytosanitary, irrigation, pest_monitoring, cultural_practice, flowering
    day: date = None
    fields: dict = field(default_factory=dict)
    supply: Optional[str] = None   # clave de catalogs.SUPPLIES


@dataclass
class QualitySim(Registered):
    stage: str = ""
    day: date = None
    fields: dict = field(default_factory=dict)


@dataclass
class WorkSim:
    employee: EmployeeSim
    day: date
    payment_type: str              # per_kg | per_day
    kg_true: float
    kg_collected: Optional[float]  # lo pesado y anotado
    rate_per_kg: Optional[float]
    day_value: Optional[float]
    total_value: float
    paid_at: Optional[date] = None


@dataclass
class HarvestSim:
    plot: "PlotSim"
    cycle: "CycleSim"
    pass_number: int
    start: date
    end: Optional[date]            # None = abierta
    rate_per_kg: float
    rate_per_day: float
    works: list = field(default_factory=list)
    family_kg: float = 0.0
    loss_fraction: float = 0.0
    total_kg: Optional[float] = None
    green: float = 0.0
    overripe: float = 0.0
    bored: float = 0.0
    cherry_eval: Optional[QualitySim] = None
    daily_kg: dict = field(default_factory=dict)   # día → kg que entran al beneficio

    @property
    def ripe(self) -> float:
        return 100.0 - self.green - self.overripe


@dataclass
class CycleSim:
    plot: "PlotSim"
    number: int
    start: date
    end: Optional[date]            # None = activo
    harvest_start: date
    flowering: date
    labors: list = field(default_factory=list)
    harvests: list = field(default_factory=list)
    nitrogen_kg: float = 0.0
    nitrogen_recommended: float = 1.0
    rain_filling: float = 0.0
    temp_mean: float = 0.0
    rust_max: float = 0.0
    effective_age: float = 0.0

    @property
    def n_index(self) -> float:
        return self.nitrogen_kg / self.nitrogen_recommended if self.nitrogen_recommended else 0.0


@dataclass
class PlotSim:
    key: str
    name: str
    variety: str
    area: float
    slope: float
    soil_type: str
    shade_type: str
    row_spacing: float
    plant_spacing: float
    planting_date: date
    altitude: float                # verdadera (latente): la finca registra la suya
    renewed_from: Optional["PlotSim"] = None
    closed_at: Optional[date] = None
    seed_origin: Optional[str] = None
    events: list = field(default_factory=list)
    soil: list = field(default_factory=list)
    cycles: list = field(default_factory=list)
    broca: dict = field(default_factory=dict)      # lunes de la semana → % en campo
    rust: dict = field(default_factory=dict)
    alert_config: Optional[dict] = None

    @property
    def trees(self) -> int:
        return int(round(self.area * 10000 / (self.row_spacing * self.plant_spacing)))

    @property
    def density(self) -> float:
        return 10000 / (self.row_spacing * self.plant_spacing)

    def zoca_dates(self) -> list[date]:
        return sorted(event.day for event in self.events if event.event_type == "zoca")

    def effective_age(self, day: date) -> float:
        starts = [self.planting_date] + [z for z in self.zoca_dates() if z <= day]
        return max((day - max(starts)).days, 0) / 365.25


@dataclass
class WetSim:
    key: str
    day: date                      # día de la recolección que se procesa
    inputs: list                   # [(HarvestSim, kg cereza)]
    status: str = "completed"
    pulped_at: Optional[datetime] = None
    fermentation_start: Optional[datetime] = None
    fermentation_end: Optional[datetime] = None
    fermentation_method: Optional[str] = None
    decided_by: Optional[str] = None
    criteria: Optional[str] = None
    ambient_temp: Optional[float] = None
    floats_kg: Optional[float] = None
    floats_method: Optional[str] = None
    wash_count: Optional[int] = None
    washed_kg: Optional[float] = None
    washed_at: Optional[datetime] = None
    # Latentes (verdaderos aunque no se registren)
    delay_h: float = 0.0
    fermentation_h: float = 0.0
    temperature: float = 0.0
    floats_true: float = 0.0
    bored: float = 0.0
    green: float = 0.0
    overripe: float = 0.0
    process_missing: dict = field(default_factory=dict)  # campo → no se registró

    @property
    def cherry_kg(self) -> float:
        return sum(kg for _, kg in self.inputs)


@dataclass
class DryingSim:
    key: str
    method: str
    other_detail: Optional[str]
    start: date
    inputs: list                   # [(WetSim, kg lavado)]
    end: Optional[date] = None     # None = en curso
    days_effort: float = 0.0       # días de secado efectivo de la tanda
    rain_mm: float = 0.0
    temp_mean: float = 0.0
    humidity_true: float = 0.0
    final_humidity: Optional[float] = None
    output_kg: Optional[float] = None
    humidity_checks: list = field(default_factory=list)
    packaging: Optional[str] = None
    sack_count: Optional[int] = None
    packed_at: Optional[date] = None
    storage_place: Optional[str] = None
    destination: Optional[str] = None
    inventory: Optional[tuple] = None       # (full_price, purchase_date) al cerrar
    later_inventory: Optional[tuple] = None  # guardado que pasa después al inventario
    quality: Optional[QualitySim] = None
    audit: dict = field(default_factory=dict)


@dataclass
class DayLaborSim:
    employee: EmployeeSim
    day: date
    activity: str
    other_detail: Optional[str]
    plot: Optional[PlotSim]
    daily_value: float
    paid_at: Optional[date] = None


@dataclass
class FarmSim:
    key: str
    index: int
    name: str
    village: str
    municipality: catalogs.Municipality
    altitude: float
    latitude: float
    longitude: float
    management: str
    drying_method: str
    drying_other_detail: Optional[str]
    mix_probability: float
    irrigates: bool
    hires: bool
    humidity_habit: float
    fermaestro: str
    criteria: str
    floats_method: str
    temp_offset: float
    rain_factor: float
    total_area: float = 0.0
    plots: list = field(default_factory=list)
    employees: list = field(default_factory=list)
    climate: dict = field(default_factory=dict)
    climate_records: list = field(default_factory=list)
    wets: list = field(default_factory=list)
    dryings: list = field(default_factory=list)
    day_labors: list = field(default_factory=list)
    alert_config: Optional[dict] = None

    @property
    def profile(self) -> rules.Management:
        return MANAGEMENT[self.management]


@dataclass
class World:
    params: Params
    enso: dict
    farms: list = field(default_factory=list)
    scenarios: list = field(default_factory=list)   # situaciones del presente aplicadas (present.py)

    def all_dryings(self):
        for farm in self.farms:
            yield from (drying for drying in farm.dryings)

    def registered(self):
        """
        (finca, grupo, registrado) de cada registro sujeto a faltantes, para
        medir el % efectivo. Lo que dejó sin registrar una situación del
        presente no cuenta: no sale del % configurado.
        """
        for farm in self.farms:
            for record in farm.climate_records:
                if not record.forced:
                    yield farm, record.group, record.recorded
            for plot in farm.plots:
                for record in plot.soil:
                    yield farm, record.group, record.recorded
                for cycle in plot.cycles:
                    for record in cycle.labors:
                        if not record.forced:
                            yield farm, record.group, record.recorded
                    for harvest in cycle.harvests:
                        if harvest.cherry_eval is not None and not harvest.cherry_eval.forced:
                            yield farm, "cherry_quality", harvest.cherry_eval.recorded
            for wet in farm.wets:
                if wet.status == "completed":
                    for missing in wet.process_missing.values():
                        yield farm, "process", not missing
            for drying in farm.dryings:
                if drying.quality is not None and not drying.quality.forced:
                    yield farm, "parchment_quality", drying.quality.recorded


# ═══════════════════════════════════════════════════════════════════════════
# Utilidades de muestreo
# ═══════════════════════════════════════════════════════════════════════════


def stream(seed: int, *parts) -> random.Random:
    """Generador independiente y reproducible para una parte del mundo."""
    return random.Random("|".join(str(part) for part in (seed, *parts)))


def truncnorm(rng: random.Random, mean: float, sd: float, low: float, high: float) -> float:
    for _ in range(100):
        value = rng.gauss(mean, sd)
        if low <= value <= high:
            return value
    return min(max(mean, low), high)


def lognormal(rng: random.Random, median: float, sigma: float) -> float:
    return median * math.exp(rng.gauss(0.0, sigma))


def choose(rng: random.Random, weights: dict):
    keys = list(weights)
    return rng.choices(keys, weights=[weights[key] for key in keys])[0]


def at(day: date, hour: float) -> datetime:
    """Instante del día en hora de Colombia."""
    return datetime.combine(day, time(0), tzinfo=BUSINESS_TZ) + timedelta(hours=hour)


def monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def next_saturday(day: date) -> date:
    return day + timedelta(days=(5 - day.weekday()) % 7 or 7)


def daterange(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


# Climatología mensual andina bimodal (mm por mes, año promedio ≈ 2.200 mm)
MONTHLY_RAIN = [120, 140, 200, 260, 240, 150, 110, 120, 180, 280, 260, 160]
WET_DAY_PROBABILITY = [0.40, 0.45, 0.55, 0.65, 0.62, 0.45, 0.35, 0.38, 0.52, 0.68, 0.66, 0.50]
SEASONAL_TEMP = [0.3, 0.4, 0.3, 0.0, -0.1, -0.2, 0.2, 0.4, 0.2, -0.2, -0.4, -0.2]
ENSO_EFFECT = {"nino": (0.70, 0.6), "nina": (1.35, -0.3), "neutral": (1.0, 0.0)}


def simulate_enso(params: Params) -> dict:
    """Fase ENSO por año, compartida por todas las fincas (el clima es regional)."""
    rng = stream(params.seed, "enso")
    return {
        year: choose(rng, {"nino": 0.25, "nina": 0.25, "neutral": 0.5})
        for year in range(params.sim_start.year, params.end_date.year + 2)
    }


# ═══════════════════════════════════════════════════════════════════════════
# Simulación de una finca
# ═══════════════════════════════════════════════════════════════════════════


class FarmSimulator:
    def __init__(self, params: Params, index: int, enso: dict, name: str):
        self.params = params
        self.index = index
        self.enso = enso
        self.name = name
        self.end = params.end_date
        self.window_start = params.window_start
        seed = params.seed
        self.rng = stream(seed, "farm", index, "profile")
        self.climate_rng = stream(seed, "farm", index, "climate")
        self.process_rng = stream(seed, "farm", index, "process")
        self.labor_rng = stream(seed, "farm", index, "payroll")
        # Faltantes: generador propio, igual con cualquier nivel (§3.6)
        self.record_rng = stream(seed, "farm", index, "records")
        self.wet_counter = 0
        self.drying_counter = 0
        self.busy: dict[date, set] = {}   # día → recolectores ya ocupados

    # ── Registro (faltantes) ──────────────────────────────────────────────

    def recorded(self, group: str) -> bool:
        draw = self.record_rng.random()
        probability = rules.missing_probability(
            self.params.missing_level, group, self.farm.profile.registration
        )
        return draw >= probability

    # ── Perfil ────────────────────────────────────────────────────────────

    def run(self) -> FarmSim:
        self.farm = self.profile()
        self.simulate_climate()
        self.create_employees()
        self.create_plots()
        queue = list(self.farm.plots)
        while queue:
            plot = queue.pop(0)
            renewal = self.simulate_plot(plot)
            if renewal is not None:
                self.farm.plots.append(renewal)
                queue.append(renewal)
        self.farm.total_area = round(sum(p.area for p in self.farm.plots if p.closed_at is None) * self.rng.uniform(1.2, 1.8), 2)
        self.process()
        self.payroll()
        self.record_climate()
        self.alert_configs()
        return self.farm

    def profile(self) -> FarmSim:
        rng = self.rng
        municipality = rng.choice(catalogs.MUNICIPALITIES)
        d = rules.DISTRIBUTIONS["farm_altitude"]
        altitude = round(truncnorm(rng, d["mean"], d["sd"], d["min"], d["max"]))
        management = choose(rng, {key: m.weight for key, m in MANAGEMENT.items()})
        method = choose(rng, {key: m.weight for key, m in DRYING_METHODS.items()})
        return FarmSim(
            key=f"F{self.index + 1:03d}",
            index=self.index,
            name=self.name,
            village=rng.choice(catalogs.VILLAGES),
            municipality=municipality,
            altitude=altitude,
            latitude=round(municipality.latitude + rng.uniform(-0.08, 0.08), 6),
            longitude=round(municipality.longitude + rng.uniform(-0.08, 0.08), 6),
            management=management,
            drying_method=method,
            drying_other_detail=rng.choice(rules.OTHER_DRYING_DETAILS) if method == "other" else None,
            mix_probability=rng.uniform(*rules.DISTRIBUTIONS["mix_probability"]),
            irrigates=rng.random() < 0.12,
            hires=rng.random() < {"good": 0.9, "medium": 0.6, "careless": 0.35}[management],
            humidity_habit=rng.gauss(*MANAGEMENT[management].humidity_habit),
            fermaestro=f"{rng.choice(catalogs.FIRST_NAMES)} {rng.choice(catalogs.SURNAMES)}",
            criteria=rng.choice(catalogs.FERMENTATION_CRITERIA),
            floats_method=rng.choice(catalogs.FLOATS_METHODS),
            temp_offset=rng.gauss(0.0, 0.6),
            rain_factor=truncnorm(rng, 1.0, 0.15, 0.7, 1.35),
        )

    # ── Clima (latente completo) ──────────────────────────────────────────

    def simulate_climate(self) -> None:
        rng = self.climate_rng
        farm = self.farm
        base = 29.2 - 0.0062 * farm.altitude + farm.temp_offset
        anomaly = 0.0
        for day in daterange(self.params.sim_start, self.end):
            rain_mult, temp_shift = ENSO_EFFECT[self.enso.get(day.year, "neutral")]
            month = day.month - 1
            anomaly = 0.7 * anomaly + rng.gauss(0.0, 0.55)
            wet = rng.random() < min(0.95, WET_DAY_PROBABILITY[month] * (0.85 + 0.15 * rain_mult))
            rain = 0.0
            if wet:
                mean_amount = MONTHLY_RAIN[month] * farm.rain_factor * rain_mult / (30.4 * WET_DAY_PROBABILITY[month])
                rain = rng.gammavariate(0.8, mean_amount / 0.8)
            t_mean = base + SEASONAL_TEMP[month] + temp_shift + anomaly - (0.4 if rain > 10 else 0.0)
            spread = max(4.0, rng.gauss(9.5, 1.2) - (2.0 if rain > 10 else 0.0))
            farm.climate[day] = DayClimate(
                t_mean=t_mean, t_min=t_mean - spread / 2, t_max=t_mean + spread / 2, rain=rain
            )

    def rain_between(self, start: date, end: date) -> float:
        return sum(self.farm.climate[d].rain for d in daterange(start, end) if d in self.farm.climate)

    def temp_between(self, start: date, end: date) -> float:
        values = [self.farm.climate[d].t_mean for d in daterange(start, end) if d in self.farm.climate]
        return sum(values) / len(values) if values else 20.0

    # ── Personas ──────────────────────────────────────────────────────────

    def create_employees(self) -> None:
        size = {"good": (6, 12), "medium": (4, 10), "careless": (3, 7)}[self.farm.management]
        for _ in range(self.rng.randint(*size)):
            self.hire(self.rng)

    def hire(self, rng: random.Random) -> EmployeeSim:
        """Un trabajador nuevo, con nombre distinto a los de la finca."""
        names = {e.full_name for e in self.farm.employees}
        while True:
            name = f"{rng.choice(catalogs.FIRST_NAMES)} {rng.choice(catalogs.SURNAMES)} {rng.choice(catalogs.SURNAMES)}"
            if name not in names:
                break
        employee = EmployeeSim(key=f"{self.farm.key}-E{len(self.farm.employees) + 1:03d}", full_name=name)
        self.farm.employees.append(employee)
        return employee

    # ── Lotes ─────────────────────────────────────────────────────────────

    def create_plots(self) -> None:
        rng = stream(self.params.seed, "farm", self.index, "plots")
        count = rng.randint(*self.params.plots_per_farm)
        names = rng.sample(catalogs.PLOT_NAMES, min(count, len(catalogs.PLOT_NAMES)))
        for n in range(count):
            name = names[n] if n < len(names) else f"Lote {n + 1}"
            age = rng.triangular(**rules.DISTRIBUTIONS["initial_age"])
            planting = self.window_start - timedelta(days=int(age * 365.25))
            self.farm.plots.append(self.new_plot(rng, f"{self.farm.key}-P{n + 1}", name, planting))

    def new_plot(
        self, rng: random.Random, key: str, name: str, planting: date,
        variety: Optional[str] = None, renewed_from: Optional[PlotSim] = None,
    ) -> PlotSim:
        d = rules.DISTRIBUTIONS
        area = renewed_from.area if renewed_from else min(
            d["plot_area"]["max"], max(d["plot_area"]["min"], lognormal(rng, d["plot_area"]["median"], d["plot_area"]["sigma"]))
        )
        return PlotSim(
            key=key,
            name=name,
            variety=variety or choose(rng, {k: v.weight for k, v in VARIETIES.items()}),
            area=round(area, 2),
            slope=round(truncnorm(rng, d["slope_pct"]["mean"], d["slope_pct"]["sd"], d["slope_pct"]["min"], d["slope_pct"]["max"]), 1),
            soil_type=choose(rng, {"Franco": 0.3, "Franco arcilloso": 0.3, "Franco arenoso": 0.2, "Arcilloso": 0.15, "Arenoso": 0.05}),
            shade_type=renewed_from.shade_type if renewed_from else choose(
                rng, {"Libre exposición": 0.35, "Guamo": 0.2, "Plátano": 0.2, "Nogal cafetero": 0.1, "Sombrío mixto": 0.15}
            ),
            row_spacing=round(rng.uniform(*d["row_spacing_m"]), 2),
            plant_spacing=round(rng.uniform(*d["plant_spacing_m"]), 2),
            planting_date=planting,
            altitude=self.farm.altitude + rng.gauss(0.0, d["plot_altitude_noise_sd"]),
            renewed_from=renewed_from,
            seed_origin="Almácigo propio" if renewed_from else None,
        )

    def season_starts(self, rng: random.Random, plot_offset: float) -> list[date]:
        """Inicio de la cosecha principal de cada año para el lote."""
        mun = self.farm.municipality
        farm_offset = stream(self.params.seed, "farm", self.index, "season").gauss(0.0, 7.0)
        starts = []
        for year in range(self.params.sim_start.year, self.end.year + 2):
            base = date(year, mun.harvest_month, mun.harvest_day)
            starts.append(base + timedelta(days=round(farm_offset + plot_offset + rng.gauss(0.0, 6.0))))
        return starts

    def simulate_plot(self, plot: PlotSim) -> Optional[PlotSim]:
        """Ciclos, sanidad, labores y cosechas del lote; devuelve su renovación si la hay."""
        rng = stream(self.params.seed, "plot", plot.key)
        seasons = self.season_starts(rng, rng.gauss(0.0, 3.0))

        # 1. Temporadas productivas y su ventana de frutos (para la sanidad)
        plans = []
        previous_end: Optional[date] = None
        renewal: Optional[PlotSim] = None
        for harvest_start in seasons:
            if plot.closed_at is not None:
                break
            flowering = harvest_start - timedelta(
                days=rules.FLOWERING_TO_HARVEST_DAYS + round(max(-14.0, min(14.0, rng.gauss(0.0, rules.FLOWERING_SD_DAYS))))
            )
            if harvest_start < self.window_start + timedelta(days=45):
                continue
            if plot.effective_age(harvest_start) < rules.MIN_PRODUCTIVE_AGE:
                continue
            if previous_end is None:
                start = max(
                    self.window_start + timedelta(days=rng.randint(0, 20)),
                    flowering - timedelta(days=rng.randint(30, 90)),
                    plot.planting_date + timedelta(days=30),
                )
            else:
                start = max(previous_end + timedelta(days=rng.randint(1, 6)),
                            flowering - timedelta(days=rng.randint(30, 90)))
            if start > self.end:
                break
            if start >= harvest_start:
                continue
            passes = self.plan_passes(rng, harvest_start)
            last_end = passes[-1][1]
            cycle_end = last_end + timedelta(days=rng.randint(2, 20))
            plans.append((start, flowering, harvest_start, passes, cycle_end))
            previous_end = cycle_end
            if cycle_end >= self.end:
                break
            # Renovación: zoca o siembra nueva después del ciclo
            age = plot.effective_age(cycle_end)
            if age >= 18 and self.farm.management != "good" and rng.random() < 0.3:
                closure = cycle_end + timedelta(days=rng.randint(15, 45))
                planting = closure + timedelta(days=rng.randint(30, 90))
                if planting <= self.end:
                    plot.closed_at = closure
                    plot.events.append(EventSim("closure", closure, "Cafetal envejecido: se renueva por siembra"))
                    renewal = self.new_plot(
                        rng, f"{plot.key}R", plot.name, planting,
                        variety=choose(rng, {"Castillo": 0.6, "Cenicafé 1": 0.3, "Tabi": 0.1}), renewed_from=plot,
                    )
            elif age >= 8 and rng.random() < {"good": 0.25, "medium": 0.2, "careless": 0.1}[self.farm.management]:
                zoca = cycle_end + timedelta(days=rng.randint(10, 40))
                if zoca <= self.end:
                    plot.events.append(EventSim("zoca", zoca, "Zoca del cafetal"))
            elif rng.random() < 0.03:
                replant = cycle_end + timedelta(days=rng.randint(10, 60))
                if replant <= self.end:
                    plot.events.append(EventSim("partial_replant", replant, "Resiembra de los árboles perdidos"))

        # 2. Sanidad semanal (broca y roya) con las decisiones del caficultor
        fruit_windows = [(flowering + timedelta(days=100), passes[-1][1]) for _, flowering, _, passes, _ in plans]
        harvest_ends = [passes[-1][1] for _, _, _, passes, _ in plans]
        monitorings, applications = self.simulate_health(rng, plot, fruit_windows, harvest_ends, plans)

        # 3. Ciclos con sus labores y cosechas
        for number, (start, flowering, harvest_start, passes, cycle_end) in enumerate(plans, start=1):
            cycle = CycleSim(
                plot=plot, number=number, start=start,
                end=cycle_end if cycle_end < self.end else None,
                harvest_start=harvest_start, flowering=flowering,
            )
            limit = min(cycle_end, self.end)
            self.cycle_labors(rng, plot, cycle, limit, monitorings, applications)
            self.cycle_latents(plot, cycle)
            self.cycle_harvests(rng, plot, cycle, passes)
            plot.cycles.append(cycle)

        # 4. Análisis de suelo del terreno
        self.soil_analyses(rng, plot)
        return renewal

    def plan_passes(self, rng: random.Random, harvest_start: date) -> list[tuple[date, date, float]]:
        count = choose(rng, rules.PASSES["counts"])
        shares = rules.PASSES["shares"][count]
        passes, start = [], harvest_start
        for share in shares:
            share = share * rng.uniform(0.85, 1.15)
            length = rng.randint(3, 8)
            end = start + timedelta(days=length - 1)
            passes.append((start, end, share))
            start = end + timedelta(days=rng.randint(*rules.PASSES["gap_days"]))
        total = sum(share for _, _, share in passes)
        return [(s, e, share / total) for s, e, share in passes]

    # ── Sanidad ───────────────────────────────────────────────────────────

    def simulate_health(self, rng, plot, fruit_windows, harvest_ends, plans):
        """Broca y roya semana a semana; devuelve los muestreos y las aplicaciones hechas."""
        profile = self.farm.profile
        broca_p = rules.RULES["broca_dynamics"].params
        rust_p = rules.RULES["rust_dynamics"].params
        susceptibility = VARIETIES[plot.variety].rust_susceptibility
        start = monday(max(self.params.sim_start, plot.planting_date))
        broca = lognormal(rng, {"good": 1.0, "medium": 1.8, "careless": 3.0}[self.farm.management], 0.4)
        rust = rng.uniform(0.0, 3.0) * susceptibility
        protected_until: Optional[date] = None
        next_monitoring = start + timedelta(days=rng.randint(0, profile.monitoring_days[1]))
        pending: list[tuple[date, str]] = []   # (fecha, objetivo) de aplicaciones decididas
        monitorings: list[tuple[date, float, float]] = []
        applications: list[tuple[date, str]] = []
        preventive = {
            flowering + timedelta(days=offset)
            for _, flowering, _, _, _ in plans
            for offset in (60, 150)
        } if self.farm.management == "good" and susceptibility > 0.5 else set()

        week = start
        while week <= self.end:
            week_end = week + timedelta(days=6)
            temp = self.temp_between(week, week_end)
            rain = self.rain_between(week, week_end)

            # Broca
            fruit = any(a <= week <= b for a, b in fruit_windows)
            leftover = (not profile.gleaning) and any(e <= week <= e + timedelta(days=56) for e in harvest_ends)
            r = broca_p["r0"] + broca_p["rT"] * (temp - 20.0) + broca_p["pressure"][self.farm.management]
            r += broca_p["r_dry"] if rain < broca_p["dry_week_mm"] else 0.0
            r += broca_p["r_fruit"] if fruit else broca_p["r_no_fruit"]
            r += broca_p["r_leftover"] if leftover else 0.0
            broca = broca + r * broca * (1.0 - broca / broca_p["K"]) + broca_p["immigration"]
            broca *= math.exp(rng.gauss(0.0, broca_p["noise_sd"]))
            if profile.gleaning and any(week <= e <= week_end for e in harvest_ends):
                broca *= broca_p["gleaning"]

            # Roya
            protected = protected_until is not None and week <= protected_until
            if rain >= rust_p["wet_week_mm"] and rust_p["t_low"] <= temp <= rust_p["t_high"]:
                growth = susceptibility * (rust_p["a"] + rust_p["b"] * rust)
                rust += growth * (0.3 if protected else 1.0)
            else:
                rust *= rust_p["decay"]

            # Aplicaciones decididas para esta semana
            for app_day, target in [p for p in pending if week <= p[0] <= week_end]:
                pending.remove((app_day, target))
                applications.append((app_day, target))
                if target == "Broca":
                    broca *= 1.0 - rng.uniform(*broca_p["control_eff"])
                elif target == "Roya":
                    rust *= rust_p["fungicide"]
                    protected_until = app_day + timedelta(weeks=rust_p["protection_weeks"])
            for day in sorted(d for d in preventive if week <= d <= week_end):
                applications.append((day, "Roya"))
                rust *= rust_p["fungicide"]
                protected_until = day + timedelta(weeks=rust_p["protection_weeks"])

            broca = min(max(broca, broca_p["min"]), 40.0)
            rust = min(max(rust, 0.0), rust_p["max"])
            plot.broca[week] = broca
            plot.rust[week] = rust

            # Muestreo del caficultor y su decisión
            while next_monitoring <= week_end:
                if next_monitoring >= week:
                    observed_broca = broca * math.exp(rng.gauss(0.0, 0.15))
                    observed_rust = rust * math.exp(rng.gauss(0.0, 0.2))
                    monitorings.append((next_monitoring, observed_broca, observed_rust))
                    if fruit and observed_broca >= profile.broca_action_pct and rng.random() < profile.action_probability:
                        pending.append((next_monitoring + timedelta(days=rng.randint(3, 12)), "Broca"))
                    if observed_rust >= 10.0 and rng.random() < profile.action_probability:
                        pending.append((next_monitoring + timedelta(days=rng.randint(3, 15)), "Roya"))
                next_monitoring += timedelta(days=rng.randint(*profile.monitoring_days))
            week += timedelta(days=7)
        return monitorings, applications

    def broca_at(self, plot: PlotSim, day: date) -> float:
        return plot.broca.get(monday(day), 1.0)

    # ── Labores del ciclo ─────────────────────────────────────────────────

    def add_labor(self, cycle: CycleSim, kind: str, group: str, day: date, fields: dict, supply: Optional[str] = None) -> None:
        cycle.labors.append(LaborSim(group=group, recorded=self.recorded(group), kind=kind, day=day, fields=fields, supply=supply))

    def cycle_labors(self, rng, plot: PlotSim, cycle: CycleSim, limit: date, monitorings, applications) -> None:
        profile = self.farm.profile
        inside = lambda day: cycle.start <= day <= limit  # noqa: E731
        cycle_days = max((cycle.end or cycle.harvest_start + timedelta(days=60)) - cycle.start, timedelta(days=1)).days
        # Lo recomendado para el ciclo: una cosecha al año (menos en cafetales jóvenes)
        age_factor = 0.75 if plot.effective_age(cycle.harvest_start) < 3 else 1.0
        cycle.nitrogen_recommended = (
            rules.RULES["nutrition"].params["n_recommended_kg_ha_year"] * plot.area * age_factor
        )

        # Floración principal y secundarias
        if inside(cycle.flowering):
            self.add_labor(cycle, "flowering", "flowering", cycle.flowering, {"intensity": "high"})
        for _ in range(rng.randint(0, 2)):
            day = cycle.flowering + timedelta(days=rng.choice([-1, 1]) * rng.randint(10, 35))
            if inside(day):
                self.add_labor(cycle, "flowering", "flowering", day, {"intensity": rng.choice(["low", "medium"])})

        # Fertilizaciones edáficas
        count = rng.randint(*profile.fertilizations)
        offsets = {3: [("start", 20, 40), ("flowering", 20, 40), ("flowering", 110, 140)],
                   2: [("flowering", 20, 40), ("flowering", 110, 140)],
                   1: [("flowering", 30, 90)], 0: []}[count]
        for anchor, low, high in offsets:
            base = cycle.start if anchor == "start" else cycle.flowering
            day = base + timedelta(days=rng.randint(low, high))
            if not inside(day):
                continue
            product = choose(rng, {"compound": 0.7, "urea": 0.15, "dap": 0.15})
            factor = {"compound": 1.0, "urea": 0.45, "dap": 0.8}[product]
            quantity = round(rng.uniform(*profile.dose_kg_ha) * factor * plot.area, 1)
            cycle.nitrogen_kg += quantity * catalogs.SUPPLIES[product].nitrogen
            self.add_labor(cycle, "fertilization", "fertilization", day, {
                "method": "soil",
                "quantity": quantity,
                "dose_per_tree_g": round(quantity * 1000 / plot.trees, 2),
                "cost": round(quantity * catalogs.supply_price(product, day), -2),
            }, supply=product)
        if self.farm.management == "good":
            for _ in range(rng.randint(1, 2)):
                day = cycle.start + timedelta(days=rng.randint(30, max(31, cycle_days - 30)))
                if inside(day):
                    liters = round(rng.uniform(2.0, 4.0) * plot.area, 1)
                    cycle.nitrogen_kg += liters * catalogs.SUPPLIES["foliar"].nitrogen
                    self.add_labor(cycle, "fertilization", "fertilization", day, {
                        "method": "foliar", "quantity": liters, "dose_per_tree_g": None,
                        "cost": round(liters * catalogs.supply_price("foliar", day), -2),
                    }, supply="foliar")

        # Muestreos de plagas (los hechos dentro del ciclo)
        for day, broca, rust in monitorings:
            if not inside(day):
                continue
            fields = {"broca_pct": round(min(broca, 100.0), 2)}
            if self.farm.management != "careless" or rng.random() < 0.5:
                fields["roya_pct"] = round(min(rust, 100.0), 2)
            worst = max(broca / 2.0, rust / 10.0)
            fields["severity"] = "high" if worst >= 2.5 else "medium" if worst >= 1.0 else "low"
            if rng.random() < 0.05:
                fields["other_pest"] = rng.choice(catalogs.OTHER_PESTS)
                fields["other_pest_pct"] = round(rng.uniform(1.0, 8.0), 2)
            self.add_labor(cycle, "pest_monitoring", "pest_monitoring", day, fields)

        # Aplicaciones fitosanitarias decididas por los muestreos
        for day, target in applications:
            if not inside(day):
                continue
            if target == "Broca":
                product, quantity, dose = "beauveria", round(rng.uniform(0.8, 1.5) * plot.area, 2), "1 kg por ha en 200 L de agua"
            else:
                product = "cyproconazole" if rng.random() < 0.7 else "copper"
                quantity = round(rng.uniform(0.4, 0.8) * plot.area, 2)
                dose = "0,5 L por ha" if product == "cyproconazole" else "2 kg por ha"
            self.add_labor(cycle, "phytosanitary", "phytosanitary", day, {
                "target": target, "quantity": quantity, "dose_description": dose,
                "cost": round(quantity * catalogs.supply_price(product, day), -2),
            }, supply=product)
        if self.farm.management != "good" and rng.random() < 0.4:
            day = cycle.start + timedelta(days=rng.randint(15, max(16, cycle_days - 15)))
            if inside(day):
                quantity = round(rng.uniform(1.5, 3.0) * plot.area, 2)
                self.add_labor(cycle, "phytosanitary", "phytosanitary", day, {
                    "target": "Maleza", "quantity": quantity, "dose_description": "Parcheo con bomba de espalda",
                    "cost": round(quantity * catalogs.supply_price("glyphosate", day), -2),
                }, supply="glyphosate")

        # Labores culturales
        wage = catalogs.day_wage
        day = cycle.start + timedelta(days=rng.randint(10, profile.weeding_days[0]))
        while inside(day):
            self.add_labor(cycle, "cultural_practice", "cultural_practice", day, {
                "practice_type": "weeding", "cost": round(max(1, round(plot.area * 2)) * wage(day), -2),
            })
            day += timedelta(days=rng.randint(*profile.weeding_days))
        if rng.random() < profile.pruning_probability:
            day = cycle.start + timedelta(days=rng.randint(10, 60))
            if inside(day):
                self.add_labor(cycle, "cultural_practice", "cultural_practice", day, {
                    "practice_type": "pruning", "cost": round(max(1, round(plot.area * 3)) * wage(day), -2),
                })
        if SHADE_LEVELS[plot.shade_type] > 0 and rng.random() < profile.shade_regulation_probability:
            day = cycle.start + timedelta(days=rng.randint(20, 90))
            if inside(day):
                self.add_labor(cycle, "cultural_practice", "cultural_practice", day, {
                    "practice_type": "shade_regulation", "cost": round(max(1, round(plot.area * 2)) * wage(day), -2),
                })
        if self.farm.management != "careless" and rng.random() < 0.15:
            day = cycle.start + timedelta(days=rng.randint(20, 120))
            if inside(day):
                self.add_labor(cycle, "cultural_practice", "cultural_practice", day, {
                    "practice_type": "amendment", "cost": round(max(1, round(plot.area)) * wage(day), -2),
                })

        # Riego en semanas secas (solo fincas con riego)
        if self.farm.irrigates:
            day = cycle.start
            while inside(day):
                if self.rain_between(day - timedelta(days=7), day) < 10:
                    self.add_labor(cycle, "irrigation", "irrigation", day, {
                        "method": rng.choice(catalogs.IRRIGATION_METHODS),
                        "duration_minutes": rng.choice([60, 90, 120, 180]),
                        "volume_liters": round(rng.uniform(4000, 9000) * plot.area, 1),
                    })
                    day += timedelta(days=rng.randint(7, 10))
                else:
                    day += timedelta(days=3)

        cycle.labors.sort(key=lambda labor: (labor.day, labor.kind))

    def cycle_latents(self, plot: PlotSim, cycle: CycleSim) -> None:
        """Variables del ciclo que entran a los mecanismos de calidad."""
        window = rules.RULES["rain_filling"].params["window_days"]
        cycle.rain_filling = self.rain_between(cycle.harvest_start - timedelta(days=window), cycle.harvest_start)
        cycle.temp_mean = self.temp_between(cycle.start, min(cycle.harvest_start, self.end))
        filling = [r for w, r in plot.rust.items() if cycle.harvest_start - timedelta(days=window) <= w <= cycle.harvest_start]
        cycle.rust_max = max(filling) if filling else 0.0
        cycle.effective_age = plot.effective_age(cycle.harvest_start)

    # ── Cosechas ──────────────────────────────────────────────────────────

    def cycle_harvests(self, rng, plot: PlotSim, cycle: CycleSim, passes) -> None:
        profile = self.farm.profile
        variety = VARIETIES[plot.variety]
        age_factor = rules._interpolate(
            [(1.8, 0.25), (2.5, 0.5), (3.5, 0.85), (4.0, 1.0), (7.0, 1.0), (10.0, 0.8), (15.0, 0.55), (20.0, 0.4)],
            cycle.effective_age,
        )
        season_kg = (
            plot.area * variety.productivity * age_factor * profile.productivity
            * (plot.density / 5000.0) ** 0.25
            * (1.0 - 0.006 * cycle.rust_max)
            * (1.0 - 0.25 * rules.water_deficit(cycle.rain_filling))
            * lognormal(rng, 1.0, rules.DISTRIBUTIONS["season_yield_sigma"])
        )
        picker = rules.DISTRIBUTIONS["picker_kg_day"]
        green_median, green_sigma = profile.green_pct
        for number, (start, end, share) in enumerate(passes, start=1):
            if start > self.end:
                break
            closed = end <= self.end
            harvest = HarvestSim(
                plot=plot, cycle=cycle, pass_number=number, start=start,
                end=end if closed else None,
                rate_per_kg=catalogs.picking_rate(start), rate_per_day=catalogs.day_wage(start),
            )
            pass_kg = season_kg * share
            harvest.family_kg = pass_kg * rng.uniform(0.0, 0.08)
            harvest.loss_fraction = rng.uniform(0.002, 0.03)   # merma mínima: los gramos redondeados nunca superan el total
            picked_target = pass_kg - harvest.family_kg

            # Composición verdadera de la cereza
            pass_factor = 1.15 if number == 1 else 1.3 if number == len(passes) else 0.9
            harvest.green = min(40.0, max(0.5, lognormal(rng, green_median, green_sigma) * pass_factor))
            harvest.overripe = min(20.0, max(0.3, lognormal(rng, 3.5 if number == len(passes) else 2.5, 0.4)))
            mid = start + (end - start) / 2
            harvest.bored = min(40.0, max(0.0, self.broca_at(plot, mid) * rng.uniform(
                rules.RULES["broca_harvest"].params["low"], rules.RULES["broca_harvest"].params["high"]
            )))

            # Recolectores y trabajo diario: nadie recoge en dos lotes el mismo día; si los
            # trabajadores de la finca no alcanzan, se contratan recolectores de temporada
            days = [d for d in daterange(start, end) if d.weekday() != 6] or [start]
            crew_size = max(2, math.ceil(picked_target / (picker["mean"] * len(days))))
            free = [e for e in self.farm.employees if not any(e.key in self.busy.get(d, ()) for d in days)]
            while len(free) < crew_size:
                free.append(self.hire(rng))
            crew = rng.sample(free, crew_size)
            for day in days:
                self.busy.setdefault(day, set()).update(e.key for e in crew)
            per_day_workers = {e.key for e in crew if rng.random() < 0.15}
            # Rendimiento de cada recolector ajustado a la cosecha del lote; varía por día (fruto
            # disponible, lluvia) y por persona
            scale = picked_target / (crew_size * len(days) * 0.92 * picker["mean"])
            for day in days:
                present = [e for e in crew if rng.random() < 0.92] or crew[:1]
                day_factor = lognormal(rng, 1.0, 0.12) * (0.8 if self.farm.climate.get(day, DayClimate(0, 0, 0, 0)).rain > 15 else 1.0)
                for employee in present:
                    weight = min(picker["max"], max(picker["min"], rng.gauss(picker["mean"], picker["sd"])))
                    kg = round(min(weight * scale * day_factor, picker["max"]), 1)
                    if day > self.end:
                        continue
                    if employee.key in per_day_workers:
                        value = harvest.rate_per_day
                        work = WorkSim(employee, day, "per_day", kg, kg if rng.random() < 0.7 else None, None, value, value)
                    else:
                        rate = harvest.rate_per_kg
                        work = WorkSim(employee, day, "per_kg", kg, kg, rate, None, round(kg * rate, 2))
                    harvest.works.append(work)
                    employee.last_work = max(employee.last_work or day, day)
            worked = sum(w.kg_true for w in harvest.works)
            family_share = harvest.family_kg / max(len(days), 1)
            for day in days:
                if day > self.end:
                    continue
                kg = sum(w.kg_true for w in harvest.works if w.day == day) + family_share
                harvest.daily_kg[day] = math.floor(kg * (1.0 - harvest.loss_fraction) * 1000) / 1000
            if closed:
                harvest.total_kg = round(worked + harvest.family_kg, 3)

            # Evaluación en cereza (muestra con error de muestreo)
            if closed or rng.random() < 0.5:
                eval_day = min(start + timedelta(days=rng.randint(0, max(0, (min(end, self.end) - start).days))), self.end)
                green = min(60.0, max(0.0, harvest.green + rng.gauss(0.0, 1.0)))
                overripe = min(30.0, max(0.0, harvest.overripe + rng.gauss(0.0, 0.8)))
                harvest.cherry_eval = QualitySim(
                    group="cherry_quality", recorded=self.recorded("cherry_quality"), stage="cherry", day=eval_day,
                    fields={
                        "ripe_pct": round(100.0 - green - overripe, 2),
                        "green_pct": round(green, 2),
                        "overripe_pct": round(overripe, 2),
                        "bored_pct": round(min(100.0, max(0.0, harvest.bored + rng.gauss(0.0, 0.4))), 2),
                    },
                )
            cycle.harvests.append(harvest)

    # ── Suelo ─────────────────────────────────────────────────────────────

    def soil_analyses(self, rng, plot: PlotSim) -> None:
        every = {"good": 730, "medium": 1100, "careless": 2000}[self.farm.management]
        day = max(self.window_start, plot.planting_date) + timedelta(days=rng.randint(30, every))
        while day <= self.end and (plot.closed_at is None or day <= plot.closed_at):
            ph = round(truncnorm(rng, 5.2, 0.5, 4.0, 7.0), 2)
            plot.soil.append(SoilSim(group="soil_analysis", recorded=self.recorded("soil_analysis"), day=day, fields={
                "ph": ph,
                "organic_matter_pct": round(truncnorm(rng, 8.0, 3.0, 2.0, 18.0), 2),
                "nitrogen": round(truncnorm(rng, 0.35, 0.1, 0.1, 0.8), 2),
                "phosphorus": round(truncnorm(rng, 12.0, 6.0, 2.0, 40.0), 2),
                "potassium": round(truncnorm(rng, 0.4, 0.15, 0.1, 1.2), 2),
                "texture": plot.soil_type,
                "laboratory": rng.choice(catalogs.LABORATORIES),
            }))
            day += timedelta(days=every + rng.randint(-60, 60))

    # ── Beneficio, secado y calidad ───────────────────────────────────────

    def process(self) -> None:
        """Beneficio diario por finca, tandas de secado y calidad en pergamino."""
        rng = self.process_rng
        farm = self.farm
        by_day: dict[date, list] = {}
        for plot in farm.plots:
            for cycle in plot.cycles:
                for harvest in cycle.harvests:
                    for day, kg in harvest.daily_kg.items():
                        by_day.setdefault(day, []).append((harvest, kg))
        for day in sorted(by_day):
            items = sorted(by_day[day], key=lambda item: (item[0].plot.key, item[0].pass_number))
            groups = [items] if len(items) > 1 and rng.random() < farm.mix_probability else [[item] for item in items]
            for group in groups:
                self.wet_processing(rng, day, [(h, kg) for h, kg in group if kg > 0])
        self.dryings(rng)

    def wet_processing(self, rng, day: date, inputs) -> None:
        if not inputs:
            return
        farm = self.farm
        profile = farm.profile
        self.wet_counter += 1
        wet = WetSim(key=f"{farm.key}-W{self.wet_counter:05d}", day=day, inputs=inputs)
        d = rules.DISTRIBUTIONS
        mode = choose(rng, dict(zip(("same", "evening", "next"), profile.delay_mix)))
        if mode == "same":
            wet.delay_h = min(6.5, max(0.5, lognormal(rng, d["delay_same_day"]["median"], d["delay_same_day"]["sigma"])))
        elif mode == "evening":
            wet.delay_h = rng.uniform(*d["delay_evening"])
        else:
            wet.delay_h = rng.uniform(*d["delay_next_morning"])
        delivery = rules.RULES["pulping_delay"].params["delivery_hour"]
        pulped = at(day, delivery + wet.delay_h)
        wet.temperature = farm.climate[day].t_mean + rng.gauss(0.0, 0.8)
        bias, spread = profile.fermentation_bias
        hours = rules.fermentation_center(wet.temperature) + rng.gauss(bias, spread)
        if rng.random() < profile.fermentation_forget:
            hours += rng.uniform(*d["fermentation_forget_extra"])
        wet.fermentation_h = min(60.0, max(5.0, hours))
        start = pulped + timedelta(hours=rng.uniform(0.2, 1.0))
        end = start + timedelta(hours=wet.fermentation_h)

        cherry = wet.cherry_kg
        bored = sum(h.bored * kg for h, kg in inputs) / cherry
        green = sum(h.green * kg for h, kg in inputs) / cherry
        overripe = sum(h.overripe * kg for h, kg in inputs) / cherry
        float_pct = min(15.0, max(0.3, 1.0 + 0.30 * bored + 0.08 * green + 0.15 * overripe + rng.gauss(0.0, 0.4)))
        floats = cherry * float_pct / 100.0
        washed = (cherry - floats) * rng.gauss(d["washed_ratio"]["mean"], d["washed_ratio"]["sd"])
        method = choose(rng, {"tank": 0.78, "dry": 0.17, "water": 0.05})
        wash_count = rng.randint(3, 4) if farm.management == "good" else rng.randint(2, 4)
        measures_temp = farm.management == "good" and rng.random() < 0.6
        wet.floats_true = floats
        wet.bored, wet.green, wet.overripe = bored, green, overripe

        # Faltantes del proceso: cada campo opcional por separado (§3.6)
        missing = {name: not self.recorded("process") for name in ("floats", "pulped", "fermentation", "method", "decided", "temp")}
        wet.process_missing = missing
        now = at(self.end, 23.99)
        if pulped > now:
            wet.status = "in_progress"     # la cereza espera el despulpado
            farm.wets.append(wet)
            return
        wet.pulped_at = None if missing["pulped"] else pulped
        wet.floats_kg = None if missing["floats"] else round(floats, 3)
        wet.floats_method = None if missing["floats"] else farm.floats_method
        wet.fermentation_method = None if missing["method"] else method
        wet.decided_by = None if missing["decided"] else farm.fermaestro
        wet.criteria = None if missing["decided"] else farm.criteria
        wet.ambient_temp = round(wet.temperature, 1) if measures_temp and not missing["temp"] else None
        wet.fermentation_start = None if missing["fermentation"] else start
        if end > now:
            wet.status = "in_progress"
            farm.wets.append(wet)
            return
        wet.fermentation_end = None if missing["fermentation"] else end
        wet.wash_count = wash_count
        wet.washed_kg = round(washed, 3)
        wet.washed_at = end + timedelta(hours=rng.uniform(0.5, 1.5))
        farm.wets.append(wet)

    def dryings(self, rng) -> None:
        farm = self.farm
        method = farm.drying_method
        profile = DRYING_METHODS[method]
        completed = sorted((w for w in farm.wets if w.status == "completed"), key=lambda w: w.washed_at)
        batch: list = []
        batch_start: Optional[date] = None
        capacity = 0.0
        fill_days = rng.randint(1, 3)

        def close_batch():
            nonlocal batch, batch_start
            if batch:
                self.drying(rng, batch_start, batch)
            batch, batch_start = [], None

        for wet in completed:
            wash_day = wet.washed_at.astimezone(BUSINESS_TZ).date()
            remaining = wet.washed_kg
            while remaining > 0.001:
                if batch and (wash_day > batch_start + timedelta(days=fill_days) or capacity <= 0.5):
                    close_batch()
                if not batch:
                    batch_start = wash_day
                    capacity = rng.uniform(*profile.capacity_kg)
                    fill_days = rng.randint(0, 2) if method == "mechanical_silo" else rng.randint(1, 3)
                portion = min(remaining, capacity)
                if remaining - portion < 5.0:   # sin restos ínfimos
                    portion = remaining
                batch.append((wet, round(portion, 3)))
                capacity -= portion
                remaining = round(remaining - portion, 3)
        close_batch()

    def drying(self, rng, start: date, inputs) -> None:
        farm = self.farm
        profile = farm.profile
        method = farm.drying_method
        mp = DRYING_METHODS[method]
        self.drying_counter += 1
        drying = DryingSim(
            key=f"{farm.key}-D{self.drying_counter:04d}", method=method,
            other_detail=farm.drying_other_detail, start=start, inputs=inputs,
        )
        last_input = max(w.washed_at.astimezone(BUSINESS_TZ).date() for w, _ in inputs)
        fill_span = (last_input - start).days
        dd = rules.RULES["drying_days"].params
        horizon = start + timedelta(days=max(1, round(mp.norm_days)))
        rain_index = self.rain_between(start, horizon) / (max(mp.norm_days, 1.0) * dd["rain_reference_mm_day"])
        temp = self.temp_between(start, horizon)
        effort = mp.norm_days * (1.0 + dd["rain_effect"] * mp.rain_sensitivity * (rain_index - 1.0))
        effort *= 1.0 - dd["temp_effect"] * (temp - 19.0)
        effort *= math.exp(rng.gauss(0.0, mp.sd_days / mp.norm_days))
        drying.days_effort = max(0.8, effort)
        end = start + timedelta(days=fill_span + max(1, math.ceil(drying.days_effort)))
        drying.rain_mm = self.rain_between(start, end)
        drying.temp_mean = self.temp_between(start, end)
        drying.humidity_true = rules.humidity_mechanism(
            farm.humidity_habit, method, drying.days_effort, drying.rain_mm
        ) + rng.gauss(0.0, rules.RULES["humidity"].params["process_sd"])
        reading = drying.humidity_true + rng.gauss(0.0, rules.DISTRIBUTIONS["meter_sd"])
        moisture = rng.gauss(rules.DISTRIBUTIONS["wet_moisture"]["mean"], rules.DISTRIBUTIONS["wet_moisture"]["sd"])
        wet_total = sum(kg for _, kg in inputs)
        output = wet_total * (1.0 - moisture) / (1.0 - drying.humidity_true / 100.0)

        # Mediciones intermedias (curva de secado)
        checks = rng.randint(*profile.humidity_checks)
        total_days = max((end - start).days, 1)
        for n in range(checks):
            fraction = (n + 1) / (checks + 1)
            day = start + timedelta(days=max(1, min(total_days - 1, round(fraction * total_days))))
            value = drying.humidity_true + (52.0 - drying.humidity_true) * math.exp(-3.2 * fraction)
            if day <= self.end and day < end:
                drying.humidity_checks.append((day, round(value + rng.gauss(0.0, 0.8), 1)))

        # Targets y auditoría: para todo secado que termina (aunque su evaluación no se registre)
        targets_noise = {key: rng.gauss(0.0, sd) for key, sd in rules.NOISE_SD.items()}
        eval_offset = rng.randint(2, 10)
        destination_draw = rng.random()
        later_draw = rng.random()
        price_factor = rng.gauss(1.03, 0.04)
        packing = (rng.randint(0, 3), rng.random(), rng.choice(catalogs.STORAGE_PLACES), rng.randint(0, 5), rng.randint(30, 90))
        parchment_recorded = self.recorded("parchment_quality")

        farm.dryings.append(drying)
        if end > self.end:
            drying.audit = {}
            return   # en curso: sin cierre ni calidad

        drying.end = end
        drying.final_humidity = round(min(30.0, max(5.0, reading)), 1)
        drying.output_kg = round(min(output, wet_total), 3)
        drying.humidity_checks = [(d, v) for d, v in drying.humidity_checks if d <= end]
        pack_delay, pack_draw, place, purchase_delay, later_delay = packing
        drying.packed_at = end + timedelta(days=pack_delay) if end + timedelta(days=pack_delay) <= self.end else None
        drying.packaging = "Bolsa GrainPro + costal de fique" if pack_draw < 0.85 else "Costal de fique"
        drying.sack_count = max(1, math.ceil(drying.output_kg / 62.5))
        drying.storage_place = place

        recent = (self.end - end).days <= 60
        weights = (0.15, 0.50, 0.35) if recent else (0.08, 0.87, 0.05)
        destination = "inventory" if destination_draw < weights[0] else "direct_sale" if destination_draw < weights[0] + weights[1] else "stored"
        if destination == "inventory" and not self.params.inventory_available:
            destination = "stored"
        drying.destination = destination
        if destination == "inventory":
            purchase = min(end + timedelta(days=purchase_delay), self.end)
            drying.inventory = (round(catalogs.carga_price(purchase) * price_factor, -3), purchase)
        elif destination == "stored" and not recent:
            # Lo guardado no se queda para siempre: entra al inventario o se vende directo
            purchase = end + timedelta(days=later_delay)
            if self.params.inventory_available and later_draw < 0.5:
                if purchase <= self.end:
                    drying.later_inventory = (round(catalogs.carga_price(purchase) * price_factor, -3), purchase)
            else:
                drying.destination = "direct_sale"

        targets = self.targets(drying, targets_noise)
        eval_day = end + timedelta(days=eval_offset)
        if eval_day <= self.end:
            drying.quality = QualitySim(
                group="parchment_quality", recorded=parchment_recorded, stage="parchment", day=eval_day,
                fields={
                    "score": round(targets["score"], 2),
                    "defects_pct": round(targets["defects_pct"], 2),
                    "yield_factor": round(targets["yield_factor"], 2),
                    "humidity_pct": round(targets["humidity_pct"], 2),
                },
            )

    def targets(self, drying: DryingSim, noise: dict) -> dict:
        """Mecanismos de calidad sobre las variables verdaderas, ponderadas por la cereza trazada."""
        by_harvest: dict = {}
        by_wet: list = []
        for wet, kg in drying.inputs:
            fraction = kg / wet.washed_kg
            traced = 0.0
            for harvest, cherry in wet.inputs:
                by_harvest[id(harvest)] = (harvest, by_harvest.get(id(harvest), (harvest, 0.0))[1] + cherry * fraction)
                traced += cherry * fraction
            by_wet.append((wet, traced))
        total = sum(kg for _, kg in by_harvest.values())

        def weighted(values) -> float:
            return sum(value * kg for value, kg in values) / total

        harvests = list(by_harvest.values())
        x = {
            "cherry_kg_traced": total,
            "bored_pct": weighted((h.bored, kg) for h, kg in harvests),
            "green_pct": weighted((h.green, kg) for h, kg in harvests),
            "overripe_pct": weighted((h.overripe, kg) for h, kg in harvests),
            "altitude": weighted((h.plot.altitude, kg) for h, kg in harvests),
            "effective_age": weighted((h.cycle.effective_age, kg) for h, kg in harvests),
            "shade_level": weighted((SHADE_LEVELS[h.plot.shade_type], kg) for h, kg in harvests),
            "cycle_temp": weighted((h.cycle.temp_mean, kg) for h, kg in harvests),
            "rain_filling_mm": weighted((h.cycle.rain_filling, kg) for h, kg in harvests),
            "n_index": weighted((h.cycle.n_index, kg) for h, kg in harvests),
            "rust_max_pct": weighted((h.cycle.rust_max, kg) for h, kg in harvests),
            "cup_base": weighted((VARIETIES[h.plot.variety].cup_base, kg) for h, kg in harvests),
            "susceptibility": weighted((VARIETIES[h.plot.variety].rust_susceptibility, kg) for h, kg in harvests),
            "pulping_delay_h": sum(w.delay_h * kg for w, kg in by_wet) / total,
            "fermentation_h": sum(w.fermentation_h * kg for w, kg in by_wet) / total,
            "fermentation_temp": sum(w.temperature * kg for w, kg in by_wet) / total,
            "drying_days_effort": drying.days_effort,
            "drying_rain_mm": drying.rain_mm,
            "humidity_true": drying.humidity_true,
        }
        x["fermentation_deviation"] = rules.fermentation_deviation(x["fermentation_h"], x["fermentation_temp"])
        norm = DRYING_METHODS[drying.method].norm_days
        components = {
            "intercept": rules.RULES["intercept"].params["q0"],
            "variety": x["cup_base"],
            "altitude": rules.q_altitude(x["altitude"]),
            "age": rules.q_age(x["effective_age"]),
            "shade_temperature": rules.q_shade(x["shade_level"], x["cycle_temp"]),
            "rain_filling": rules.q_rain_filling(x["rain_filling_mm"]),
            "nutrition": rules.q_nutrition(x["n_index"]),
            "green": rules.q_green(x["green_pct"]),
            "fermentation": rules.q_fermentation(x["fermentation_h"], x["fermentation_temp"]),
            "pulping_delay": rules.q_pulping_delay(x["pulping_delay_h"]),
            "drying": rules.q_drying(x["humidity_true"], x["drying_days_effort"], norm, x["drying_rain_mm"]),
        }
        q_s = sum(components.values())
        raw = {
            "score": rules.score_from_latent(q_s) + rules.score_broca(x["bored_pct"]) + noise["score"],
            "defects_pct": rules.defects_mechanism(q_s, x["bored_pct"], x["green_pct"], x["humidity_true"]) + noise["defects"],
            "yield_factor": rules.yield_mechanism(
                x["bored_pct"], x["rust_max_pct"], x["susceptibility"], rules.water_deficit(x["rain_filling_mm"]), x["altitude"]
            ) + noise["yield"],
            "humidity_pct": x["humidity_true"] + noise["humidity"],
        }
        targets, clipped = {}, {}
        for name, value in raw.items():
            low, high = rules.TARGET_RANGES[name]
            targets[name] = min(high, max(low, value))
            clipped[name] = targets[name] != value
        drying.audit = {
            "management": self.farm.management,
            **{f"x_{k}": v for k, v in x.items()},
            **{f"c_{k}": v for k, v in components.items()},
            "q_s": q_s,
            **{f"noise_{k}": v for k, v in noise.items()},
            **{f"target_{k}": v for k, v in targets.items()},
            **{f"clipped_{k}": v for k, v in clipped.items()},
        }
        return targets

    # ── Jornales y pagos ──────────────────────────────────────────────────

    def payroll(self) -> None:
        """Jornales de las labores hechas (fincas que contratan) y fechas de pago."""
        rng = self.labor_rng
        farm = self.farm
        activity = {"fertilization": "fertilization", "phytosanitary": "phytosanitary"}
        practices = {"weeding": "weeding", "pruning": "pruning", "shade_regulation": "shade_regulation"}
        if farm.hires:
            for plot in farm.plots:
                for cycle in plot.cycles:
                    for labor in cycle.labors:
                        kind = activity.get(labor.kind) or (
                            practices.get(labor.fields.get("practice_type")) if labor.kind == "cultural_practice" else None
                        )
                        if kind is None:
                            continue
                        crew = rng.sample(farm.employees, min(len(farm.employees), rng.randint(1, 3)))
                        days = max(1, round(plot.area * rng.uniform(0.6, 1.2)))
                        for offset in range(days):
                            day = labor.day + timedelta(days=offset)
                            if day > self.end:
                                break
                            for employee in crew:
                                farm.day_labors.append(DayLaborSim(
                                    employee, day, kind, None, plot if rng.random() < 0.8 else None, catalogs.day_wage(day),
                                ))
                                employee.last_work = max(employee.last_work or day, day)
            # Mantenimiento general de la finca
            day = self.window_start + timedelta(days=rng.randint(10, 40))
            while day <= self.end:
                employee = rng.choice(farm.employees)
                farm.day_labors.append(DayLaborSim(
                    employee, day, "maintenance", None, None, catalogs.day_wage(day),
                ))
                employee.last_work = max(employee.last_work or day, day)
                day += timedelta(days=rng.randint(25, 60))

        # Pago semanal: el sábado siguiente; algunos se pagan tarde
        late = farm.profile.pays_late
        def pay(day: date) -> Optional[date]:
            paid = next_saturday(day)
            if rng.random() < late:
                paid += timedelta(weeks=rng.randint(2, 6))
            return paid if paid <= self.end else None

        for plot in farm.plots:
            for cycle in plot.cycles:
                for harvest in cycle.harvests:
                    for work in harvest.works:
                        work.paid_at = pay(work.day)
        for labor in farm.day_labors:
            labor.paid_at = pay(labor.day)
        farm.day_labors.sort(key=lambda labor: (labor.day, labor.employee.key, labor.activity))

        cutoff = self.end - timedelta(days=365)
        for employee in farm.employees:
            employee.active = employee.last_work is not None and employee.last_work >= cutoff

    # ── Registro del clima ────────────────────────────────────────────────

    def record_climate(self) -> None:
        farm = self.farm
        rng = stream(self.params.seed, "farm", self.index, "climate-records")
        thermometer = farm.management == "good" or rng.random() < 0.3
        for day in daterange(self.window_start, self.end):
            weather = farm.climate[day]
            record = ClimateRec(
                group="climate", recorded=self.recorded("climate"), day=day,
                rainfall_mm=round(weather.rain, 1),
                temp_min=round(weather.t_min + rng.gauss(0.0, 0.3), 1) if thermometer else None,
                temp_max=round(weather.t_max + rng.gauss(0.0, 0.3), 1) if thermometer else None,
                observations="Granizada" if weather.rain > 60 and rng.random() < 0.05 else None,
            )
            if record.temp_min is not None and record.temp_max is not None and record.temp_min > record.temp_max:
                record.temp_min, record.temp_max = record.temp_max, record.temp_min
            farm.climate_records.append(record)

    # ── Configuración de alertas ──────────────────────────────────────────

    def alert_configs(self) -> None:
        rng = stream(self.params.seed, "farm", self.index, "alerts")
        farm = self.farm
        if rng.random() < 0.3:
            config = {}
            if farm.drying_method == "mechanical_silo":
                config["max_drying_days"] = 4
            if farm.altitude < 1400:
                config["min_fermentation_hours"] = 8
                config["max_fermentation_hours"] = 20
            if farm.management == "good":
                config["fertilization_reminder_days"] = 100
                config["broca_alert_pct"] = 1.5
            farm.alert_config = config or {"inactivity_alert_days": 30}
        # Quien riega activa su recordatorio de riego (desactivado por defecto)
        if farm.irrigates:
            farm.alert_config = {**(farm.alert_config or {}), "irrigation_reminder_days": 12}
        for plot in farm.plots:
            if plot.variety == "Geisha" and rng.random() < 0.5:
                plot.alert_config = {"broca_alert_pct": 1.0}


# ═══════════════════════════════════════════════════════════════════════════
# Entrada
# ═══════════════════════════════════════════════════════════════════════════


def farm_names(params: Params) -> list[str]:
    """Un nombre distinto por finca, sorteado del catálogo con un generador propio."""
    available = len(catalogs.FARM_NAMES)
    if params.farms > available:
        raise ValueError(f"El catálogo tiene {available} nombres de finca: no se pueden generar {params.farms} fincas")
    return stream(params.seed, "farm-names").sample(catalogs.FARM_NAMES, params.farms)


def simulate(params: Params, log=None) -> World:
    """Simula el mundo; `log(mensaje)` recibe el avance finca por finca."""
    from scripts.farm_ml.present import apply_present

    log = log or (lambda message: None)
    names = farm_names(params)
    enso = simulate_enso(params)
    world = World(params=params, enso=enso)
    for index, name in enumerate(names):
        farm = FarmSimulator(params, index, enso, name).run()
        world.farms.append(farm)
        cycles = sum(len(plot.cycles) for plot in farm.plots)
        closed = sum(1 for drying in farm.dryings if drying.end is not None)
        log(f"[{index + 1}/{params.farms}] {farm.name} ({farm.municipality.name}): "
            f"{len(farm.plots)} lotes, {cycles} ciclos, {len(farm.wets)} beneficios, {closed} secados cerrados")
    log("Aplicando las situaciones del presente…")
    apply_present(world)
    return world
