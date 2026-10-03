"""
Formas de las funciones de respuesta del generador (generador-sintetico-ml §3.3).

Verifican la dirección y la forma que el documento exige a cada regla, no
sus magnitudes (que son decisiones de simulación).
"""

import pytest

from scripts.farm_ml import rules


def slope(function, x, h=0.01):
    return (function(x + h) - function(x - h)) / (2 * h)


def test_every_rule_separates_evidence_from_decision():
    """G6: cada regla declara dirección, fuente, forma y parámetros."""
    for name, rule in rules.RULES.items():
        assert rule.direction and rule.source and rule.form, name
        assert rule.params, name


def test_broca_on_score_is_a_sigmoid_with_threshold_and_floor():
    s = rules.score_broca
    floor = rules.RULES["broca_score"].params["floor"]
    x0 = rules.RULES["broca_score"].params["x0"]
    assert s(0.0) == pytest.approx(0.0)
    assert abs(s(1.0)) < 0.5                       # plana a baja infestación
    assert s(10.0) < 0.95 * floor                  # piso: el café ya salió de grado
    values = [s(x / 10) for x in range(0, 150)]
    assert all(b <= a for a, b in zip(values, values[1:]))   # siempre empeora
    steepest = max(range(1, 149), key=lambda i: abs(values[i + 1] - values[i - 1])) / 10
    assert x0 - 1.0 <= steepest <= x0 + 1.0        # mayor pendiente en la inflexión


def test_broca_on_defects_is_almost_linear():
    d = lambda b: rules.defects_mechanism(0.5, b, 5.0, 11.0)  # noqa: E731
    low, high = d(4.0) - d(2.0), d(10.0) - d(8.0)
    assert 1.0 < high / low < 1.5                  # leve aceleración, no umbral


def test_fermentation_window_moves_with_temperature():
    assert rules.fermentation_center(24.0) < rules.fermentation_center(20.0) < rules.fermentation_center(17.0)
    center = rules.fermentation_center(20.0)
    assert rules.q_fermentation(center + 2.5, 20.0) == 0.0
    assert rules.q_fermentation(center - 2.5, 20.0) == 0.0
    # Larga penaliza más que corta a la misma distancia
    assert rules.q_fermentation(center + 8, 20.0) < rules.q_fermentation(center - 8, 20.0) < 0
    # Las mismas horas son sobrefermentación con calor y no con frío
    assert rules.q_fermentation(20.0, 25.0) < rules.q_fermentation(20.0, 18.0)


def test_pulping_delay_penalty_is_continuous_and_accelerates():
    q = rules.q_pulping_delay
    assert q(3.0) == q(6.0) == 0.0
    steps = [q(h) - q(h + 3) for h in (6, 9, 12, 15)]
    assert all(0 < a < b for a, b in zip(steps, steps[1:]))


def test_nutrition_has_diminishing_returns():
    q = rules.q_nutrition
    assert q(0.0) < 0 < q(1.0)
    assert q(1.5) > q(1.0)                         # el exceso no es neutro…
    assert q(1.5) - q(1.0) < q(1.0) - q(0.5)       # …pero rinde menos


def test_altitude_improves_cup_with_saturation():
    q = rules.q_altitude
    assert q(1200) < q(1500) < q(1800)
    assert slope(q, 1300) > 3 * slope(q, 1850)


def test_age_curve_rises_holds_and_declines():
    q = rules.q_age
    assert q(1) < q(4) == q(6) == q(8)
    assert q(15) < q(12) < q(8)


def test_shade_helps_in_warm_zones_only():
    assert rules.q_shade(0.0, 23.0) == 0.0
    assert rules.q_shade(0.8, 23.0) > 0
    assert rules.q_shade(0.8, 17.0) < 0


def test_humidity_fast_drying_overdries_more_than_slow_drying_wets():
    base = rules.humidity_mechanism(11.0, "marquesina", 10.0, 80.0)
    fast = rules.humidity_mechanism(11.0, "marquesina", 8.0, 64.0) - base
    slow = rules.humidity_mechanism(11.0, "marquesina", 12.0, 96.0) - base
    assert fast < 0 < slow
    assert abs(fast) > abs(slow)


def test_missing_tolerance_is_statistical():
    small, large = rules.missing_tolerance(0.4, 200), rules.missing_tolerance(0.4, 20000)
    assert small > large == rules.MISSING_TOLERANCE_MIN
    assert small == pytest.approx(4 * (0.4 * 0.6 / 200) ** 0.5)


def test_missing_probability_follows_the_farm_habit():
    assert rules.missing_probability("none", "climate", 1.5) == 0.0
    realistic = rules.MISSING_LEVELS["realistic"]["climate"]
    assert rules.missing_probability("realistic", "climate", 1.0) == pytest.approx(realistic)
    assert rules.missing_probability("realistic", "climate", 0.6) < realistic
    assert rules.missing_probability("realistic", "soil_analysis", 2.0) <= 0.97
