"""
Reglas del generador de datos sintéticos (generador-sintetico-ml §3).

Cada regla separa la evidencia de la decisión de modelado (decisión G6):

- `direction`: el sentido del efecto, respaldado por la fuente.
- `source`: de dónde sale esa dirección.
- `form`: la forma funcional elegida (por tramos, saturante, sigmoide…).
- `params`: la magnitud. **Siempre es una decisión de simulación**: la
  literatura respalda la dirección, no la ubicación de un umbral ni su
  pendiente.

Las funciones de respuesta de este archivo son puras (sin base de datos ni
azar) y se aplican sobre los valores **verdaderos** del mundo simulado, no
sobre lo registrado: lo que el caficultor anota llega con faltantes y error
de medición, igual que en la realidad.

Unidades canónicas, sin conversiones implícitas (§3.3): altitud m s.n.m. ·
temperatura °C · lluvia mm · humedad, broca, roya, verdes y defectos % (0–100)
· fermentación y demora al despulpado horas · secado días · pesos kg · edad
años · score puntos SCA · yield_factor kg de pergamino por 70 kg de excelso.

Cambiar cualquier parámetro cambia el dataset: se sube `RULES_VERSION`. La
tupla `RULES_VERSION + seed + fecha final` identifica un dataset.
"""

import math
from dataclasses import dataclass, field

RULES_VERSION = "1.1.0"


@dataclass(frozen=True)
class Rule:
    direction: str
    source: str
    form: str
    params: dict
    note: str = ""


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _interpolate(points: list[tuple[float, float]], x: float) -> float:
    """Interpolación lineal por tramos; constante fuera de los extremos."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


# ═══════════════════════════════════════════════════════════════════════════
# Perfiles de variedad y sombrío
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Variety:
    cup_base: float          # aporte a la calidad sensorial latente q_s
    rust_susceptibility: float  # 0 = resistente, 1 = muy susceptible
    productivity: float      # kg de cereza por ha y temporada en plena producción
    weight: float            # frecuencia entre los lotes sintéticos


# Los nombres son los de las sugerencias de la interfaz (labels.ts).
VARIETIES: dict[str, Variety] = {
    "Castillo": Variety(cup_base=0.00, rust_susceptibility=0.10, productivity=10500, weight=0.38),
    "Cenicafé 1": Variety(cup_base=0.05, rust_susceptibility=0.08, productivity=10000, weight=0.12),
    "Colombia": Variety(cup_base=-0.05, rust_susceptibility=0.20, productivity=9500, weight=0.08),
    "Caturra": Variety(cup_base=0.10, rust_susceptibility=1.00, productivity=8500, weight=0.16),
    "Típica": Variety(cup_base=0.20, rust_susceptibility=0.90, productivity=6000, weight=0.06),
    "Borbón": Variety(cup_base=0.35, rust_susceptibility=0.90, productivity=6500, weight=0.07),
    "Tabi": Variety(cup_base=0.25, rust_susceptibility=0.15, productivity=8000, weight=0.06),
    "Geisha": Variety(cup_base=0.90, rust_susceptibility=0.80, productivity=5000, weight=0.07),
}

# Nivel de sombrío 0–1 por tipo (sugerencias de la interfaz)
SHADE_LEVELS: dict[str, float] = {
    "Libre exposición": 0.0,
    "Plátano": 0.4,
    "Nogal cafetero": 0.6,
    "Guamo": 0.7,
    "Sombrío mixto": 0.8,
}

RULES: dict[str, Rule] = {}

RULES["variety_cup"] = Rule(
    direction="cada variedad tiene un perfil de taza propio (base) e independiente de su resistencia a roya",
    source="Cenicafé: Castillo y Cenicafé 1 con taza comparable a Caturra y resistencia a roya; Geisha y Borbón de taza alta",
    form="aporte aditivo constante por variedad sobre q_s (tabla VARIETIES)",
    params={name: v.cup_base for name, v in VARIETIES.items()},
    note="Es solo la base: su expresión depende de ambiente y manejo, no es un ranking determinante.",
)

# ═══════════════════════════════════════════════════════════════════════════
# Calidad sensorial latente q_s y score
# ═══════════════════════════════════════════════════════════════════════════

RULES["intercept"] = Rule(
    direction="—",
    source="—",
    form="constante de q_s",
    params={"q0": 0.65},
    note="Ubica el score típico alrededor de 82 puntos.",
)

RULES["altitude"] = Rule(
    direction="mayor altitud → grano más denso y ácido → mejor taza, con saturación",
    source="Cenicafé y protocolo SCA: la altitud se asocia a mayor densidad y acidez",
    form="A·tanh((alt − a0)/s) − penalización cuadrática suave sobre a_hi",
    params={"A": 0.9, "a0": 1350.0, "s": 300.0, "a_hi": 1950.0, "k_hi": 0.3, "w_hi": 200.0},
    note="Óptimo amplio 1.500–1.900 m, sin umbral.",
)


def q_altitude(altitude: float) -> float:
    p = RULES["altitude"].params
    value = p["A"] * math.tanh((altitude - p["a0"]) / p["s"])
    if altitude > p["a_hi"]:
        value -= p["k_hi"] * ((altitude - p["a_hi"]) / p["w_hi"]) ** 2
    return value


RULES["age"] = Rule(
    direction="la calidad sube con la edad del cultivo hasta ~4 años, se sostiene y decae en cafetales viejos sin zoca",
    source="Ciclo productivo del cafeto (Cenicafé): renovación por zoca o siembra cada 5–8 cosechas",
    form="lineal por tramos sobre la edad efectiva (desde siembra o última zoca)",
    params={"points": [(0.0, -0.5), (4.0, 0.0), (8.0, 0.0), (12.0, -0.15), (20.0, -0.6)]},
)


def q_age(effective_age: float) -> float:
    return _interpolate(RULES["age"].params["points"], effective_age)


RULES["shade_temperature"] = Rule(
    direction="el sombrío mejora la taza en zonas cálidas y es casi neutro (leve costo) en zonas frías",
    source="Regulación térmica del sombrío en cafetales (Cenicafé, sistemas agroforestales)",
    form="nivel·(B·clip((T − T0)/ΔT, 0, 1) − costo) — interacción sombra × temperatura",
    params={"B": 0.45, "T0": 19.0, "dT": 3.0, "cost": 0.08},
)


def q_shade(shade_level: float, temperature: float) -> float:
    p = RULES["shade_temperature"].params
    warmth = _clip((temperature - p["T0"]) / p["dT"], 0.0, 1.0)
    return shade_level * (p["B"] * warmth - p["cost"])


RULES["rain_filling"] = Rule(
    direction="lluvia en el llenado del grano con zona óptima: déficit → grano vano; exceso → fermentos y roya",
    source="Fisiología del llenado del fruto y balance hídrico (Cenicafé)",
    form="penalización cuadrática fuera de [opt_low, opt_high], con tope",
    params={
        "window_days": 120, "opt_low": 450.0, "opt_high": 1100.0,
        "deficit_coef": 0.5, "deficit_scale": 250.0, "deficit_cap": 0.8,
        "excess_coef": 0.35, "excess_scale": 300.0, "excess_cap": 0.6,
    },
    note="La ventana son los 120 días previos al inicio de la cosecha.",
)


def q_rain_filling(rain_mm: float) -> float:
    p = RULES["rain_filling"].params
    if rain_mm < p["opt_low"]:
        return -min(p["deficit_cap"], p["deficit_coef"] * ((p["opt_low"] - rain_mm) / p["deficit_scale"]) ** 2)
    if rain_mm > p["opt_high"]:
        return -min(p["excess_cap"], p["excess_coef"] * ((rain_mm - p["opt_high"]) / p["excess_scale"]) ** 2)
    return 0.0


def water_deficit(rain_mm: float) -> float:
    """Déficit hídrico normalizado 0–1 en el llenado (alimenta el vaneo del yield_factor)."""
    low = RULES["rain_filling"].params["opt_low"]
    return _clip((low - rain_mm) / low, 0.0, 1.0)


RULES["nutrition"] = Rule(
    direction="insuficiente → peor; adecuada → mejor; exceso → beneficio marginal decreciente (no neutro)",
    source="Respuesta del café a la fertilización con saturación (Cenicafé, recomendación por análisis)",
    form="a·(1 − exp(−k·n)) − b, con n = N aplicado / N recomendado en el ciclo",
    params={"a": 0.45, "k": 2.2, "b": 0.30, "n_recommended_kg_ha_year": 300.0},
)


def q_nutrition(n_index: float) -> float:
    p = RULES["nutrition"].params
    return p["a"] * (1.0 - math.exp(-p["k"] * max(n_index, 0.0))) - p["b"]


RULES["green"] = Rule(
    direction="más frutos verdes → astringencia y defecto físico → peor taza",
    source="Cenicafé: recolección selectiva; los inmaduros bajan la calidad",
    form="−c·G^e (convexa creciente)",
    params={"c": 0.03, "e": 1.25},
    note="La magnitud relativa frente a otros factores es decisión de simulación.",
)


def q_green(green_pct: float) -> float:
    p = RULES["green"].params
    return -p["c"] * max(green_pct, 0.0) ** p["e"]


RULES["fermentation"] = Rule(
    direction="fermentación fuera de su ventana → peor taza; corta penaliza poco, larga penaliza fuerte (vinagre)",
    source="Cenicafé: punto de lavado; la ventana se acorta con temperatura ambiente mayor",
    form="ventana móvil: centro(T) = c20 − slope·(T − 20), tolerancia ±tol; potencias a cada lado, con tope",
    params={
        "c20": 16.0, "slope": 1.5, "center_min": 8.0, "center_max": 22.0, "tol": 3.0,
        "short_coef": 0.04, "short_exp": 1.5, "long_coef": 0.09, "long_exp": 1.4, "cap": 3.0,
    },
)


def fermentation_center(temperature: float) -> float:
    p = RULES["fermentation"].params
    return _clip(p["c20"] - p["slope"] * (temperature - 20.0), p["center_min"], p["center_max"])


def fermentation_deviation(hours: float, temperature: float) -> float:
    """Horas por encima (+) o por debajo (−) del centro de la ventana."""
    return hours - fermentation_center(temperature)


def q_fermentation(hours: float, temperature: float) -> float:
    p = RULES["fermentation"].params
    d = fermentation_deviation(hours, temperature)
    if d < -p["tol"]:
        penalty = p["short_coef"] * (-d - p["tol"]) ** p["short_exp"]
    elif d > p["tol"]:
        penalty = p["long_coef"] * (d - p["tol"]) ** p["long_exp"]
    else:
        penalty = 0.0
    return -min(p["cap"], penalty)


RULES["pulping_delay"] = Rule(
    direction="más horas entre la recolección y el despulpado → fermentación indeseada → peor taza",
    source="Cenicafé: despulpar el mismo día de la recolección",
    form="−c·max(0, h − h0)^e: continua desde ~6 h y acelerando después de ~12 h (sin salto)",
    params={"h0": 6.0, "c": 0.012, "e": 1.7, "cap": 2.0, "delivery_hour": 16},
    note=(
        "Convención compartida con features.py: la cereza de un día de recolección se entrega a las "
        "16:00 (hora de Colombia) de su fecha; la demora es despulpado − esa hora."
    ),
)


def q_pulping_delay(hours: float) -> float:
    p = RULES["pulping_delay"].params
    return -min(p["cap"], p["c"] * max(0.0, hours - p["h0"]) ** p["e"])


RULES["drying_quality"] = Rule(
    direction=(
        "secado muy rápido → sobresecado (humedad < 10 %: grano quebradizo, taza plana); "
        "muy lento con lluvia → riesgo de moho y fermento; humedad alta → moho"
    ),
    source="Cenicafé: secado a 10–12 % de humedad",
    form="potencia bajo 10 % + penalización lineal por días de exceso × lluvia + lineal sobre 12,5 %",
    params={
        "over_coef": 0.30, "over_exp": 1.3, "slow_factor": 1.4, "slow_coef": 0.06,
        "rain_scale": 80.0, "wet_threshold": 12.5, "wet_coef": 0.25,
    },
    note="Se usa «sobresecado», no «cristalizado».",
)


def q_drying(humidity: float, days: float, norm_days: float, rain_mm: float) -> float:
    p = RULES["drying_quality"].params
    over = p["over_coef"] * max(0.0, 10.0 - humidity) ** p["over_exp"]
    slow_days = max(0.0, days - p["slow_factor"] * norm_days)
    slow = p["slow_coef"] * slow_days * (1.0 + rain_mm / p["rain_scale"])
    wet = p["wet_coef"] * max(0.0, humidity - p["wet_threshold"])
    return -(over + slow + wet)


RULES["score"] = Rule(
    direction="score = base + aporte sensorial no lineal de q_s + efecto de broca",
    source="Protocolo SCA (puntaje 0–100)",
    form="68 + 22·σ(q_s) + broca_score(b) + ε_s",
    params={"base": 68.0, "span": 22.0},
)


def score_from_latent(q_s: float) -> float:
    p = RULES["score"].params
    return p["base"] + p["span"] * _sigmoid(q_s)


RULES["broca_score"] = Rule(
    direction="% de grano brocado ↑ → score ↓, con efecto de umbral",
    source=(
        "Cenicafé, daño por Hypothenemus hampei; la selección de flotes y la trilla "
        "remueven parte del grano brocado"
    ),
    form="sigmoide normalizada (piso, x0, k): plana a baja infestación, aceleración y piso",
    params={"x0": 4.0, "k": 1.2, "floor": -12.0},
    note=(
        "x0 NO es el umbral económico de acción del MIB (2 %, usado en broca_alert_pct). "
        "La fuente respalda que existe un efecto de umbral y su dirección, no la ubicación ni la pendiente."
    ),
)


def score_broca(bored_pct: float) -> float:
    p = RULES["broca_score"].params
    at_zero = _sigmoid(-p["k"] * p["x0"])
    value = (_sigmoid(p["k"] * (bored_pct - p["x0"])) - at_zero) / (1.0 - at_zero)
    return p["floor"] * value


# ═══════════════════════════════════════════════════════════════════════════
# Defectos (mecanismo propio, G8)
# ═══════════════════════════════════════════════════════════════════════════

RULES["defects"] = Rule(
    direction=(
        "la broca aporta defecto físico directo (casi lineal); los verdes aportan inmaduros; "
        "el sobresecado aporta quebrados; solo una fracción menor viene de q_s"
    ),
    source="Clasificación de defectos del café verde (NTC 2324, SCA)",
    form="base + rango·(1 − σ(q_s)) + a·b + c·b² + g·G^e + o·max(0,10−h)^oe + w·max(0,h−12,5)",
    params={
        "base": 2.2, "span": 1.6, "broca_lin": 0.55, "broca_quad": 0.012,
        "green_coef": 0.05, "green_exp": 1.3, "over_coef": 0.5, "over_exp": 1.4, "wet_coef": 0.3,
    },
)


def defects_mechanism(q_s: float, bored_pct: float, green_pct: float, humidity: float) -> float:
    p = RULES["defects"].params
    return (
        p["base"]
        + p["span"] * (1.0 - _sigmoid(q_s))
        + p["broca_lin"] * bored_pct
        + p["broca_quad"] * bored_pct ** 2
        + p["green_coef"] * max(green_pct, 0.0) ** p["green_exp"]
        + p["over_coef"] * max(0.0, 10.0 - humidity) ** p["over_exp"]
        + p["wet_coef"] * max(0.0, humidity - 12.5)
    )


# ═══════════════════════════════════════════════════════════════════════════
# Factor de rendimiento (mecanismo físico, independiente de q_s)
# ═══════════════════════════════════════════════════════════════════════════

RULES["yield_factor"] = Rule(
    direction=(
        "kg de pergamino seco para 70 kg de excelso (menor = mejor): sube con broca, con roya "
        "(según susceptibilidad) y con vaneo por déficit hídrico; baja con la densidad de la altura"
    ),
    source="Término estándar del gremio cafetero colombiano; rango típico 88–105",
    form="92 + a·b + r·roya·susc + v·déficit² − d·tanh((alt − a0)/s) + ε_y",
    params={"base": 93.0, "broca": 0.5, "rust": 0.10, "vaneo": 6.0, "density": 2.5, "a0": 1350.0, "s": 350.0},
)


def yield_mechanism(
    bored_pct: float, rust_max_pct: float, susceptibility: float, deficit: float, altitude: float
) -> float:
    p = RULES["yield_factor"].params
    return (
        p["base"]
        + p["broca"] * bored_pct
        + p["rust"] * rust_max_pct * susceptibility
        + p["vaneo"] * deficit ** 2
        - p["density"] * math.tanh((altitude - p["a0"]) / p["s"])
    )


# ═══════════════════════════════════════════════════════════════════════════
# Secado y humedad (solo proceso de secado, independiente de q_s)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DryingMethod:
    norm_days: float        # días típicos con clima normal
    sd_days: float
    humidity_offset: float  # sesgo del punto de recogida por método
    capacity_kg: tuple[float, float]  # café lavado por tanda (rango)
    rain_sensitivity: float  # cuánto alarga el secado la lluvia del periodo
    weight: float


DRYING_METHODS: dict[str, DryingMethod] = {
    "marquesina": DryingMethod(10.0, 1.8, 0.00, (250, 1200), 0.6, 0.45),
    "elba": DryingMethod(12.0, 2.2, 0.10, (400, 1600), 0.8, 0.20),
    "patio": DryingMethod(9.0, 2.0, -0.25, (600, 2500), 1.3, 0.18),
    "mechanical_silo": DryingMethod(1.6, 0.4, -0.6, (800, 4000), 0.0, 0.10),
    "other": DryingMethod(11.0, 2.2, 0.05, (200, 800), 0.9, 0.07),
}

OTHER_DRYING_DETAILS = ["Carpa solar", "Camilla", "Secador solar parabólico casero"]

RULES["humidity"] = Rule(
    direction=(
        "la humedad final depende solo del proceso de secado: método, rapidez (días frente a lo "
        "normal del método), lluvia del periodo y el punto de recogida del caficultor"
    ),
    source="Cenicafé: se recoge entre 10 % y 12 %; secado rápido tiende a sobresecar",
    form=(
        "hábito + sesgo(método) + v_rápido·min(0, lentitud − 1) + v_lento·max(0, lentitud − 1) "
        "+ l·(lluvia diaria − referencia) + ε_proc, lentitud = días / días normales del método; "
        "laboratorio = verdadera + ε_h"
    ),
    params={"fast_coef": 3.5, "slow_coef": 2.0, "rain_coef": 0.04, "rain_reference_mm_day": 8.0, "process_sd": 0.25},
    note=(
        "Asimétrico: el secado rápido sobreseca más de lo que el lento humedece (entre una revisión y la "
        "siguiente el grano pierde humedad de más). Mecanismo casi determinista a propósito: sirve de "
        "sanity check de la ruta secado → target."
    ),
)

RULES["drying_days"] = Rule(
    direction="el secado se alarga con lluvia y frío; el silo mecánico casi no depende del clima",
    source="Cenicafé: marquesina y elba 8–15 días; silo 1–2 días",
    form="días normales·(1 + s·sensibilidad·(índice de lluvia − 1))·(1 − t·(T − 19))·lognormal",
    params={"rain_effect": 0.25, "rain_reference_mm_day": 9.0, "temp_effect": 0.04},
    note="La referencia de lluvia es la de la temporada de cosecha, que coincide con la época lluviosa.",
)


def humidity_mechanism(habit: float, method: str, days: float, rain_mm: float) -> float:
    p = RULES["humidity"].params
    profile = DRYING_METHODS[method]
    slowness = days / profile.norm_days
    rain_per_day = rain_mm / max(days, 1.0)
    return (
        habit + profile.humidity_offset
        + p["fast_coef"] * min(0.0, slowness - 1.0)
        + p["slow_coef"] * max(0.0, slowness - 1.0)
        + p["rain_coef"] * (rain_per_day - p["rain_reference_mm_day"])
    )


# ═══════════════════════════════════════════════════════════════════════════
# Ruido de los targets (§3.5)
# ═══════════════════════════════════════════════════════════════════════════

NOISE_SD = {
    "score": 1.5,      # puntos SCA: variabilidad sensorial entre catadores y tazas
    "defects": 0.6,    # pp: conteo de defectos en una muestra de 350 g
    "yield": 2.0,      # kg: variación de la trilla de muestra
    "humidity": 0.3,   # pp: medición de laboratorio
}
# σ de defectos baja de 1,2 (valor inicial del documento) a 0,6: con 1,2 el
# piso físico (0 %) recortaba más del 0,1 % de los valores (§3.5).

# Rangos físicos de los targets: el recorte es la última defensa y se cuenta.
TARGET_RANGES = {
    "score": (0.0, 100.0),
    "defects_pct": (0.0, 100.0),
    "yield_factor": (70.0, 140.0),
    "humidity_pct": (5.0, 25.0),
}
MAX_CLIP_SHARE = 0.001

# ═══════════════════════════════════════════════════════════════════════════
# Sanidad: broca y roya (procesos semanales del mundo simulado)
# ═══════════════════════════════════════════════════════════════════════════

RULES["broca_dynamics"] = Rule(
    direction="la broca crece con calor, sequía, frutos en el árbol y frutos sin recoger; baja con control y repase",
    source="Cenicafé, manejo integrado de la broca (MIB)",
    form=(
        "logística semanal con inmigración: B ← B + r·B·(1 − B/K) + inm, "
        "r = r0 + rT·(T − 20) + r_seca + r_frutos + presión(manejo)"
    ),
    params={
        "r0": 0.03, "rT": 0.02, "r_dry": 0.03, "dry_week_mm": 15.0, "r_fruit": 0.02, "r_no_fruit": -0.035,
        "r_leftover": 0.04, "pressure": {"good": 0.0, "medium": 0.004, "careless": 0.008},
        "immigration": 0.03, "K": 14.0, "noise_sd": 0.08, "control_eff": (0.45, 0.70),
        "gleaning": 0.7, "min": 0.2,
    },
    note="La presión por manejo resume vecinos sin control y frutos caídos: no se registra.",
)

RULES["broca_harvest"] = Rule(
    direction="la infestación en campo es un indicador previo del % de cereza brocada en la cosecha",
    source="Cenicafé: el muestreo en campo anticipa el daño en cosecha",
    form="bored = B(semana de la pasada)·U(a, b)",
    params={"low": 0.8, "high": 1.2},
    note="Las aplicaciones entre el muestreo y la recolección ya bajaron B: la atenuación es parte del proceso.",
)

RULES["rust_dynamics"] = Rule(
    direction="la roya crece con lluvia prolongada según la susceptibilidad de la variedad; baja en seco y con fungicida",
    source="Cenicafé: la resistencia genética de Castillo y Cenicafé 1 controla la roya",
    form="semanal: si semana lluviosa y templada R ← R + susc·(a + b·R); si no R ← R·decay",
    params={"wet_week_mm": 25.0, "t_low": 17.0, "t_high": 24.5, "a": 0.6, "b": 0.12, "decay": 0.93,
            "fungicide": 0.5, "protection_weeks": 6, "max": 60.0},
)

# ═══════════════════════════════════════════════════════════════════════════
# Manejo de la finca (latente: no se guarda en la base, sí en la auditoría)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Management:
    weight: float
    fertilizations: tuple[int, int]        # aplicaciones edáficas por ciclo
    dose_kg_ha: tuple[float, float]        # kg de producto por ha y aplicación
    monitoring_days: tuple[int, int]       # cada cuántos días muestrea plagas
    broca_action_pct: float                # umbral con el que aplica control
    action_probability: float
    weeding_days: tuple[int, int]
    pruning_probability: float
    shade_regulation_probability: float
    gleaning: bool                         # repase al final de la cosecha
    green_pct: tuple[float, float]         # mediana y dispersión log del % de verdes
    delay_mix: tuple[float, float, float]  # mismo día / tarde-noche / día siguiente
    fermentation_bias: tuple[float, float] # sesgo y dispersión de las horas frente al centro
    fermentation_forget: float             # probabilidad de olvidar el lavado (cola larga)
    humidity_habit: tuple[float, float]    # punto de recogida (media, sd)
    humidity_checks: tuple[int, int]
    productivity: float
    registration: float                    # multiplicador de faltantes (más alto = registra menos)
    pays_late: float                       # probabilidad de pagar tarde la recolección


MANAGEMENT: dict[str, Management] = {
    "good": Management(
        weight=0.30, fertilizations=(3, 3), dose_kg_ha=(600, 720), monitoring_days=(25, 35),
        broca_action_pct=2.0, action_probability=0.95, weeding_days=(60, 85),
        pruning_probability=0.6, shade_regulation_probability=0.7, gleaning=True,
        green_pct=(3.0, 0.35), delay_mix=(0.92, 0.06, 0.02), fermentation_bias=(0.0, 1.8),
        fermentation_forget=0.01, humidity_habit=(10.8, 0.3), humidity_checks=(2, 4),
        productivity=1.15, registration=0.6, pays_late=0.02,
    ),
    "medium": Management(
        weight=0.45, fertilizations=(2, 2), dose_kg_ha=(450, 600), monitoring_days=(45, 70),
        broca_action_pct=3.0, action_probability=0.8, weeding_days=(90, 130),
        pruning_probability=0.3, shade_regulation_probability=0.3, gleaning=False,
        green_pct=(6.0, 0.40), delay_mix=(0.60, 0.26, 0.14), fermentation_bias=(0.5, 3.0),
        fermentation_forget=0.04, humidity_habit=(11.1, 0.35), humidity_checks=(0, 2),
        productivity=1.0, registration=1.0, pays_late=0.08,
    ),
    "careless": Management(
        weight=0.25, fertilizations=(0, 1), dose_kg_ha=(250, 400), monitoring_days=(90, 150),
        broca_action_pct=5.0, action_probability=0.45, weeding_days=(150, 220),
        pruning_probability=0.1, shade_regulation_probability=0.05, gleaning=False,
        green_pct=(11.0, 0.45), delay_mix=(0.36, 0.30, 0.34), fermentation_bias=(2.0, 5.0),
        fermentation_forget=0.12, humidity_habit=(11.6, 0.5), humidity_checks=(0, 0),
        productivity=0.75, registration=1.45, pays_late=0.30,
    ),
}

# ═══════════════════════════════════════════════════════════════════════════
# Distribuciones de entrada (§3.4): ninguna uniforme entre mínimo y máximo
# ═══════════════════════════════════════════════════════════════════════════

DISTRIBUTIONS = {
    # Altitud de la finca: normal truncada, concentrada en 1.400–1.800 m
    "farm_altitude": {"mean": 1600.0, "sd": 190.0, "min": 1200.0, "max": 2000.0},
    "plot_altitude_noise_sd": 40.0,
    # Área del lote (ha): lognormal
    "plot_area": {"median": 1.2, "sigma": 0.6, "min": 0.3, "max": 6.0},
    # Edad del cultivo al inicio de la ventana (años): triangular
    "initial_age": {"low": 0.5, "high": 20.0, "mode": 6.0},
    "row_spacing_m": (1.2, 2.0),
    "plant_spacing_m": (1.0, 1.5),
    "slope_pct": {"mean": 30.0, "sd": 12.0, "min": 5.0, "max": 70.0},
    # Producción: dispersión log de la temporada de un lote
    "season_yield_sigma": 0.15,
    # Recolección: kg de cereza por recolector y día
    "picker_kg_day": {"mean": 100.0, "sd": 25.0, "min": 30.0, "max": 200.0},
    # Demora al despulpado (h) por modo: mismo día (lognormal), tarde-noche y día siguiente
    "delay_same_day": {"median": 2.5, "sigma": 0.45},
    "delay_evening": (5.0, 10.0),
    "delay_next_morning": (13.0, 19.0),
    # Cola de fermentación por olvido del lavado (h extra)
    "fermentation_forget_extra": (10.0, 22.0),
    # Conversión cereza → café lavado (baba retirada) y humedad del café lavado
    "washed_ratio": {"mean": 0.445, "sd": 0.012},
    "wet_moisture": {"mean": 0.55, "sd": 0.012},
    # Medidor de humedad del caficultor (error de lectura)
    "meter_sd": 0.35,
    # Mezclas en el beneficio: probabilidad de juntar lotes del mismo día
    "mix_probability": (0.7, 0.95),
}

# Pasadas de la temporada: número y reparto de la producción
PASSES = {"counts": {1: 0.15, 2: 0.45, 3: 0.40},
          "shares": {1: [1.0], 2: [0.55, 0.45], 3: [0.3, 0.45, 0.25]},
          "gap_days": (12, 25)}

FLOWERING_TO_HARVEST_DAYS = 224   # ≈ 32 semanas (dashboards-alertas §5)
FLOWERING_SD_DAYS = 7.0
MIN_PRODUCTIVE_AGE = 1.8          # años de edad efectiva para la primera cosecha

# ═══════════════════════════════════════════════════════════════════════════
# Datos faltantes (§3.6): probabilidad de que el caficultor NO registre
# ═══════════════════════════════════════════════════════════════════════════

MISSING_LEVELS: dict[str, dict[str, float]] = {
    "none": {},
    "realistic": {
        "soil_analysis": 0.70,
        "climate": 0.50,
        "pest_monitoring": 0.40,
        "flowering": 0.40,
        "irrigation": 0.30,
        "cultural_practice": 0.30,
        "fertilization": 0.15,
        "phytosanitary": 0.15,
        "cherry_quality": 0.25,
        "process": 0.05,
        "parchment_quality": 0.03,
    },
}
# Diferencia aceptada entre el % efectivo y el configurado: 4 desviaciones de una
# binomial con ese tamaño, y nunca menos de 3 puntos (con miles de registros)
MISSING_TOLERANCE_SIGMAS = 4.0
MISSING_TOLERANCE_MIN = 0.03


def missing_tolerance(probability: float, n: int) -> float:
    return max(MISSING_TOLERANCE_MIN, MISSING_TOLERANCE_SIGMAS * math.sqrt(probability * (1 - probability) / max(n, 1)))


def missing_probability(level: str, group: str, registration: float) -> float:
    """Probabilidad de no registrar, ajustada por el hábito de registro de la finca."""
    base = MISSING_LEVELS[level].get(group, 0.0)
    return _clip(base * registration, 0.0, 0.97)


# ═══════════════════════════════════════════════════════════════════════════
# Validación (§3.7): masa por zona en las variables con umbral
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Zone:
    variable: str
    cuts: tuple[float, float]          # límites entre las tres zonas
    labels: tuple[str, str, str]
    min_share: tuple[float, float, float]  # masa mínima por zona (fracción de secados)


ZONES: list[Zone] = [
    Zone("bored_pct", (3.0, 5.0), ("plana < 3 %", "inflexión 3–5 %", "piso > 5 %"), (0.30, 0.08, 0.08)),
    Zone("fermentation_deviation", (-3.0, 3.0), ("corta", "en ventana", "larga"), (0.04, 0.40, 0.10)),
    Zone("humidity_true", (10.0, 12.0), ("< 10 %", "10–12 %", "> 12 %"), (0.05, 0.50, 0.05)),
    Zone("pulping_delay_h", (6.0, 12.0), ("< 6 h", "6–12 h", "> 12 h"), (0.30, 0.08, 0.08)),
]

# Correlación esperada altitud–temperatura media de la finca: fuerte pero no perfecta
ALTITUDE_TEMPERATURE_CORRELATION = (-0.995, -0.6)


@dataclass
class Components:
    """Componentes de q_s de un secado, para el artefacto de auditoría."""

    values: dict[str, float] = field(default_factory=dict)

    @property
    def q_s(self) -> float:
        return sum(self.values.values())
