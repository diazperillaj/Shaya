"""
Situaciones del presente (generador-sintetico-ml §3.2, dashboards-alertas §4).

El mundo simulado termina en una finca que opera con orden: lo que ocurre se
registra a tiempo (salvo los faltantes). La realidad tiene además deslices
recientes que el dashboard debe mostrar: una pasada que nadie cerró, un
lavado o un secado sin registrar, una finca que dejó de anotar, una
evaluación pendiente, una pérdida en el secado.

Este paso elige, con su propio generador aleatorio, a lo sumo un caso de
cada situación entre los que la fecha final permite (una pasada sin cerrar
necesita una cosecha de hace más de 30 días, por ejemplo) y lo aplica sobre
lo registrado más reciente. No toca el histórico ni los targets de los
secados ya evaluados, y deja las mismas invariantes que el resto del mundo.
"""

import math
from datetime import timedelta

from scripts.farm_ml.world import DryingSim, World, stream

QUIET_DAYS = 60             # una finca que dejó de registrar hace dos meses
OPEN_PASS_DAYS = 30         # la pasada lleva abierta más que el umbral de la alerta
STALLED_DAYS = (2, 4)       # un lavado sin registrar de hace 2 a 4 días
UNCLOSED_START_DAYS = 16    # un secado sin cerrar que empezó hace más de 15 días
RECENT_DAYS = 30


def apply_present(world: World) -> None:
    rng = stream(world.params.seed, "present")
    end = world.params.end_date
    for name, scenario in SCENARIOS:
        candidates = scenario.candidates(world, end)
        if candidates:
            choice = candidates[rng.randrange(len(candidates))]
            world.scenarios.append(f"{name}: {scenario.apply(world, end, choice, rng)}")


# ── Pasada sin cerrar → harvest_open_too_long ─────────────────────────────


class ForgottenPass:
    """
    El caficultor no cerró la última pasada de la temporada: el ciclo no se
    pudo cerrar y las labores de la temporada siguiente quedaron en él.
    """

    @staticmethod
    def candidates(world, end):
        found = []
        for farm in world.farms:
            for plot in farm.plots:
                if len(plot.cycles) < 2:
                    continue
                previous, current = plot.cycles[-2], plot.cycles[-1]
                if current.end is not None or current.harvests or not previous.harvests or previous.end is None:
                    continue
                last = previous.harvests[-1]
                if last.end is None or last.start >= end - timedelta(days=OPEN_PASS_DAYS):
                    continue
                if any(event.day > previous.end for event in plot.events):
                    continue
                found.append((farm, plot))
        return found

    @staticmethod
    def apply(world, end, choice, rng):
        farm, plot = choice
        previous, current = plot.cycles[-2], plot.cycles[-1]
        last = previous.harvests[-1]
        last.end = None
        last.total_kg = None
        previous.end = None
        previous.labors = sorted(previous.labors + current.labors, key=lambda labor: (labor.day, labor.kind))
        plot.cycles.remove(current)
        return f"finca {farm.name}, lote {plot.name}: pasada {last.pass_number} abierta desde {last.start}"


# ── Finca en silencio → cycle_inactive ────────────────────────────────────


class QuietFarm:
    """Una finca fuera de temporada que dejó de registrar labores y clima hace dos meses."""

    @staticmethod
    def candidates(world, end):
        since = end - timedelta(days=QUIET_DAYS)
        found = []
        for farm in world.farms:
            active = [c for p in farm.plots for c in p.cycles if c.end is None]
            if not active or any(c.start > since for c in active):
                continue
            busy = any(h.start > since or (h.end or end) > since for c in active for h in c.harvests)
            busy = busy or any(w.day > since for w in farm.wets)
            if not busy:
                found.append(farm)
        return found

    @staticmethod
    def apply(world, end, farm, rng):
        since = end - timedelta(days=QUIET_DAYS)
        dropped = 0
        for plot in farm.plots:
            for cycle in plot.cycles:
                if cycle.end is not None:
                    continue
                for labor in cycle.labors:
                    if labor.day > since and labor.recorded:
                        labor.recorded, labor.forced = False, True
                        dropped += 1
        for record in farm.climate_records:
            if record.day > since and record.recorded:
                record.recorded, record.forced = False, True
                dropped += 1
        return f"finca {farm.name}: sin registros desde {since} ({dropped} registros sin anotar)"


# ── Lavado sin registrar → processing_stalled ─────────────────────────────


class StalledWash:
    """Un beneficio reciente cuyo lavado nadie registró: sigue «fermentando» en el sistema."""

    @staticmethod
    def candidates(world, end):
        low, high = (end - timedelta(days=d) for d in reversed(STALLED_DAYS))
        found = []
        for farm in world.farms:
            for wet in farm.wets:
                if wet.status != "completed" or wet.fermentation_start is None or not low <= wet.day <= high:
                    continue
                dryings = [d for d in farm.dryings if any(w is wet for w, _ in d.inputs)]
                # Solo si su café está en un único secado en curso: o no es el primero que lo
                # inició, o es su único aporte (y el secado no llegó a existir)
                if len(dryings) == 1 and dryings[0].end is None and (
                    dryings[0].inputs[0][0] is not wet or len(dryings[0].inputs) == 1
                ):
                    found.append((farm, wet, dryings[0]))
                elif not dryings:
                    found.append((farm, wet, None))
        return found

    @staticmethod
    def apply(world, end, choice, rng):
        farm, wet, drying = choice
        if drying is not None:
            drying.inputs = [(w, kg) for w, kg in drying.inputs if w is not wet]
            if not drying.inputs:
                farm.dryings.remove(drying)
        wet.status = "in_progress"
        wet.fermentation_end = None
        wet.wash_count = None
        wet.washed_kg = None
        wet.washed_at = None
        return f"finca {farm.name}: beneficio {wet.key} sin lavado registrado desde {wet.day}"


# ── Secado sin cerrar → drying_too_long ───────────────────────────────────


class UnclosedDrying:
    """Un secado que terminó hace unos días pero sigue abierto en el sistema."""

    @staticmethod
    def candidates(world, end):
        return [
            (farm, drying)
            for farm in world.farms
            for drying in farm.dryings
            if drying.end is not None
            and drying.start <= end - timedelta(days=UNCLOSED_START_DAYS)
            and drying.end >= end - timedelta(days=10)
        ]

    @staticmethod
    def apply(world, end, choice, rng):
        farm, drying = choice
        reopen(drying)
        return f"finca {farm.name}: secado {drying.key} abierto desde {drying.start}"


def reopen(drying: DryingSim) -> None:
    drying.end = None
    drying.final_humidity = drying.output_kg = None
    drying.packaging = drying.sack_count = drying.packed_at = drying.storage_place = None
    drying.destination = drying.inventory = drying.later_inventory = drying.quality = None
    drying.audit = {}


# ── Evaluaciones pendientes → drying_without_quality, harvest_without_quality ─


class PendingParchmentEval:
    """Un secado cerrado hace más de 7 días sin evaluar (si ya lo hay por azar, no hace falta)."""

    @staticmethod
    def candidates(world, end):
        window = [
            (farm, drying)
            for farm in world.farms
            for drying in farm.dryings
            if drying.end is not None and end - timedelta(days=RECENT_DAYS) <= drying.end <= end - timedelta(days=7)
        ]
        if any(drying.quality is None or not drying.quality.recorded for _, drying in window):
            return []
        return window

    @staticmethod
    def apply(world, end, choice, rng):
        farm, drying = choice
        drying.quality.recorded, drying.quality.forced = False, True
        return f"finca {farm.name}: secado {drying.key} sin evaluación en pergamino"


class PendingCherryEval:
    @staticmethod
    def candidates(world, end):
        return [
            (farm, harvest)
            for farm in world.farms
            for plot in farm.plots
            for cycle in plot.cycles
            for harvest in cycle.harvests
            if harvest.end is not None and harvest.end > end - timedelta(days=RECENT_DAYS)
            and harvest.cherry_eval is not None and harvest.cherry_eval.recorded
        ]

    @staticmethod
    def apply(world, end, choice, rng):
        farm, harvest = choice
        harvest.cherry_eval.recorded, harvest.cherry_eval.forced = False, True
        return f"finca {farm.name}, lote {harvest.plot.name}: pasada {harvest.pass_number} sin evaluación en cereza"


# ── Pérdida en el secado → yield_below_history ────────────────────────────


class DryingLoss:
    """Parte del pergamino se perdió en el secado (lluvia, animales): el rendimiento cae."""

    @staticmethod
    def candidates(world, end):
        window = end - timedelta(days=RECENT_DAYS)
        found = []
        for farm in world.farms:
            history = [d for d in farm.dryings if d.end is not None and window - timedelta(days=365) <= d.end < window]
            if len(history) < 3:
                continue
            found += [(farm, d) for d in farm.dryings if d.end is not None and d.end >= window]
        return found

    @staticmethod
    def apply(world, end, choice, rng):
        farm, drying = choice
        lost = rng.uniform(0.2, 0.28)
        drying.output_kg = round(drying.output_kg * (1 - lost), 3)
        drying.sack_count = max(1, math.ceil(drying.output_kg / 62.5))
        return f"finca {farm.name}: secado {drying.key} perdió {lost:.0%} del pergamino"


SCENARIOS = [
    ("pasada sin cerrar", ForgottenPass),
    ("finca sin registros", QuietFarm),
    ("lavado sin registrar", StalledWash),
    ("secado sin cerrar", UnclosedDrying),
    ("secado sin evaluar", PendingParchmentEval),
    ("cosecha sin evaluar", PendingCherryEval),
    ("pérdida en el secado", DryingLoss),
]
