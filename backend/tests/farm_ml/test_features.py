"""
Extracción de features del modelo de calidad (generador-sintetico-ml §4, §7.5).

La garantía contra un error compartido entre entrenamiento y proyección: un
caso con valores calculados a mano (incluida una mezcla de dos lotes con
pesos distintos) y la comparación con las variables verdaderas del mundo
simulado, independiente del modelo.
"""

import math
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pytest
from sqlalchemy import func

from app.farm_operations.ml import features as ml
from app.farm_operations.ml.features import (
    FEATURE_NAMES,
    build_features,
    cycle_origins,
    drying_origins,
    fill_future_stages,
    nitrogen_fraction,
    reference_values,
    to_matrix,
    vocabularies,
)
from app.farm_operations.models import CropCycle, Harvest, PestMonitoring, Plot
from app.models.product import Product, ProductTypeEnum
from scripts.farm_ml import dataset, rules
from scripts.farm_ml.audit import audit_rows
from scripts.farm_ml.generate_synthetic import generate
from scripts.farm_ml.world import Params
from tests.farm_ml.blend import build_blend


def years(start: date, end: date) -> float:
    return (end - start).days / 365.25


@pytest.fixture
def blend(db_session):
    return build_blend(db_session)


def test_blend_is_weighted_by_the_traced_cherry(db_session, blend):
    [origin] = drying_origins(db_session, [blend["drying"].id])
    assert origin.as_of == date(2025, 10, 15)
    assert origin.cycles == {blend["cycle_a"].id: pytest.approx(250), blend["cycle_b"].id: pytest.approx(50)}
    assert origin.wets == {blend["wet_1"].id: pytest.approx(100), blend["wet_2"].id: pytest.approx(200)}

    [row] = build_features(db_session, [origin])
    v = row.values
    wa, wb = 250 / 300, 50 / 300
    # Antes de la cosecha, por ciclo hasta el inicio de su primera pasada (A: 1 oct, B: 2 oct)
    assert v["variety"] == "Caturra" and v["shade_type"] == "Libre" and v["soil_type"] == "Franco"
    assert v["altitude"] == pytest.approx(1600)
    assert v["effective_age_years"] == pytest.approx(
        wa * years(date(2022, 3, 1), date(2025, 10, 1)) + wb * years(date(2020, 6, 1), date(2025, 10, 2)))
    assert v["density_trees_ha"] == pytest.approx(wa * 5000 + wb * 10000 / 1.5)
    assert v["soil_ph"] == pytest.approx(5.2) and v["soil_om_pct"] == pytest.approx(8)
    # Lluvia: promedio de los días registrados × 121 días. A ve 10 y 20; B, 40 (su registro), 20 y 30
    assert v["rain_mm_filling"] == pytest.approx(wa * 15 * 121 + wb * 30 * 121)
    assert v["temp_avg_cycle"] == pytest.approx(wa * 20 + wb * 19.5)
    assert v["n_fertilizations"] == pytest.approx(wa * 2)
    assert v["n_kg_ha"] == pytest.approx(wa * 46 / 2.0)       # urea 100 kg × 46 % en 2 ha; el KCl no tiene N
    assert v["days_since_last_fert"] == pytest.approx(153)    # solo A: del 1 de mayo al 1 de octubre
    assert v["n_phyto_apps"] == pytest.approx(wa)
    assert v["broca_pct_last"] == pytest.approx(3)
    assert v["roya_pct_max"] == pytest.approx(12)             # el 30 % de mayo es anterior al llenado
    assert v["n_weedings"] == pytest.approx(1) and v["n_prunings"] == pytest.approx(wa)
    # Cosecha: la evaluación posterior al cierre del secado no cuenta
    assert v["days_flowering_to_harvest"] == pytest.approx(wa * 223 + wb * 215)
    assert v["pass_number"] == pytest.approx(1) and v["cherry_kg"] == pytest.approx(wa * 600 + wb * 300)
    assert v["ripe_pct"] == pytest.approx(wa * 90 + wb * 80)
    assert v["green_pct"] == pytest.approx(wa * 5 + wb * 10)
    assert v["bored_pct"] == pytest.approx(wa * 2 + wb * 4)
    # Beneficio: pesos 100 (beneficio 1) y 200 (beneficio 2)
    assert v["floats_pct"] == pytest.approx(5)                # 10 kg de 200; el 2 no registró flotes
    assert v["hours_harvest_to_pulp"] == pytest.approx((2 * 100 + 15 * 200) / 300)
    assert v["fermentation_hours"] == pytest.approx((16 * 100 + 24 * 200) / 300)
    assert v["fermentation_temp_c"] == pytest.approx(20)
    assert v["process_day_temp_c"] == pytest.approx(19)       # clima del 2 de octubre; el 3 no tiene registro
    assert v["fermentation_method"] == "dry"
    # Secado
    assert v["drying_method"] == "marquesina" and v["drying_days"] == pytest.approx(10)
    assert v["rain_mm_drying"] == pytest.approx(5 * 11)
    assert v["final_humidity_pct"] == pytest.approx(11.5)
    assert row.stages == {"pre", "harvest", "wet", "drying"} and row.completeness == 1.0


def test_active_cycle_uses_only_what_already_happened(db_session, blend):
    """Proyección: un ciclo sin cosechar mide todo a `as_of` y no tiene etapas de cosecha ni proceso."""
    plot = Plot(farm=blend["farm"], name="C", variety="Geisha", planting_date=date(2022, 3, 1))
    cycle = CropCycle(plot=plot, cycle_number=1, start_date=date(2026, 1, 1))
    db_session.add(cycle)
    db_session.flush()
    db_session.add_all([
        PestMonitoring(crop_cycle_id=cycle.id, monitoring_date=date(2026, 3, 1), broca_pct=Decimal(2)),
        PestMonitoring(crop_cycle_id=cycle.id, monitoring_date=date(2026, 6, 1), broca_pct=Decimal(7)),  # futuro
    ])
    db_session.flush()

    [row] = build_features(db_session, cycle_origins(db_session, [cycle.id], as_of=date(2026, 4, 1)))
    assert row.stages == {"pre"}
    assert row.values["effective_age_years"] == pytest.approx(years(date(2022, 3, 1), date(2026, 4, 1)))
    assert row.values["broca_pct_last"] == pytest.approx(2)
    assert all(row.values[f.name] is None for f in ml.FEATURES if f.stage != "pre")
    assert row.completeness < 1.0


def test_active_cycle_with_an_open_pass_weighs_what_was_picked(db_session, blend):
    cycle = blend["cycle_a"]
    open_pass = Harvest(crop_cycle_id=cycle.id, pass_number=2, start_date=date(2025, 10, 20), status="open")
    db_session.add(open_pass)
    db_session.flush()
    [origin] = cycle_origins(db_session, [cycle.id], as_of=date(2025, 10, 25))
    assert origin.harvests == {blend["harvest_a"].id: pytest.approx(600), open_pass.id: pytest.approx(1.0)}
    assert set(origin.wets) == {blend["wet_1"].id, blend["wet_2"].id}
    assert origin.wets[blend["wet_1"].id] == pytest.approx(100)    # solo la cereza de este ciclo
    assert origin.dryings == {blend["drying"].id: pytest.approx(250)}


@pytest.mark.parametrize("composition, name, expected", [
    ("N 46 %", "Urea", 0.46),
    ("N 17 % · P 6 % · K 18 % · Mg 2 %", None, 0.17),
    ("Nitrógeno total (N) 46 %", None, 0.46),
    (None, "DAP 18-46-0", 0.18),
    ("K 60 %", "Cloruro de potasio", 0.0),
    (None, "Urea", None),
    ("Hongo entomopatógeno", None, None),
])
def test_nitrogen_fraction(composition, name, expected):
    assert nitrogen_fraction(composition, name) == (pytest.approx(expected) if expected is not None else None)


def test_conventions_match_the_generator_rules():
    """La ventana del llenado y la hora de entrega son las mismas en las reglas y en las features."""
    assert ml.FILLING_DAYS == rules.RULES["rain_filling"].params["window_days"]
    assert ml.DELIVERY_HOUR == rules.RULES["pulping_delay"].params["delivery_hour"]


def test_matrix_and_future_stages():
    rows = [{"variety": "Caturra", "altitude": 1600.0}, {"variety": "Castillo", "altitude": float("nan")}]
    vocab = vocabularies(rows)
    assert vocab["variety"] == ["Castillo", "Caturra"]
    matrix = to_matrix(rows + [{"variety": "Geisha"}], vocab)
    j = FEATURE_NAMES.index("variety")
    assert matrix[:, j].tolist()[:2] == [1.0, 0.0] and math.isnan(matrix[2, j])   # categoría desconocida: faltante
    assert np.isnan(matrix[1, FEATURE_NAMES.index("altitude")])

    farm = {"fermentation_hours": 18.0, "drying_method": "marquesina"}
    world = {"fermentation_hours": 16.0, "drying_days": 12.0, "drying_method": "elba", "bored_pct": 2.0}
    filled = fill_future_stages({"altitude": 1600.0, "bored_pct": None}, {"pre", "harvest"}, farm, world)
    assert filled["fermentation_hours"] == 18.0 and filled["drying_method"] == "marquesina"
    assert filled["drying_days"] == 12.0          # la finca no tiene el dato: el global
    assert filled["bored_pct"] is None            # la cosecha ya ocurrió: lo no registrado sigue faltante
    assert reference_values([{"altitude": 1.0}, {"altitude": 3.0}, {"altitude": None}])["altitude"] == 2.0


def test_features_recover_the_true_values_of_the_simulated_world(db_session):
    """
    Sin faltantes, lo que la extracción calcula desde la base coincide con lo
    que el mundo simulado usó para los targets: misma ponderación por la
    cereza trazada, mismas ventanas y la misma convención de entrega.
    """
    db_session.add(Product(name="Pergamino", quantity=0, type=ProductTypeEnum.other, active=True,
                           generates_inventory=False))
    db_session.flush()
    params = Params(end_date=date(2026, 1, 31), farms=1, plots_per_farm=(2, 3), years=3, seed=4, missing_level="none")
    result = generate(db_session, params)
    truth = {row["drying_id"]: row for row in audit_rows(result.world, result.persisted) if row["drying_id"]}
    rows = dataset.extract(db_session)
    assert len(rows) >= 30 and all(row["drying_id"] in truth for row in rows)
    # El clima se registra desde el inicio de la ventana: la lluvia del llenado solo se compara
    # cuando sus 120 días caen dentro
    origins = {o.key: o for o in drying_origins(db_session, [row["drying_id"] for row in rows])}
    first = dict(db_session.query(Harvest.crop_cycle_id, func.min(Harvest.start_date)).group_by(Harvest.crop_cycle_id))
    filling_recorded = 0
    for row in rows:
        x = truth[row["drying_id"]]
        assert row["hours_harvest_to_pulp"] == pytest.approx(x["x_pulping_delay_h"], abs=0.01)
        assert row["fermentation_hours"] == pytest.approx(x["x_fermentation_h"], abs=0.01)
        assert row["effective_age_years"] == pytest.approx(x["x_effective_age"], abs=0.01)
        # La lluvia diaria se guarda con un decimal: error de redondeo de hasta 0,05 mm por día
        assert row["rain_mm_drying"] == pytest.approx(x["x_drying_rain_mm"], abs=0.05 * (row["drying_days"] + 1))
        if min(first[c] for c in origins[row["drying_id"]].cycles) - timedelta(days=120) >= params.window_start:
            filling_recorded += 1
            assert row["rain_mm_filling"] == pytest.approx(x["x_rain_filling_mm"], abs=0.05 * 121)
        # La evaluación en cereza mide los frutos con su error de muestreo (σ 0,4 y 1 punto)
        assert row["bored_pct"] == pytest.approx(x["x_bored_pct"], abs=1.6)
        assert row["green_pct"] == pytest.approx(x["x_green_pct"], abs=4.0)
    assert filling_recorded >= 20
