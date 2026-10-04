"""
Mundo simulado del generador, sin base de datos (generador-sintetico-ml §3).

Determinismo, independencia de los faltantes e invariantes que la base
también exige (balance de masas, ciclos sin solaparse).
"""

from collections import defaultdict
from datetime import date

import pytest

from scripts.farm_ml import catalogs
from scripts.farm_ml.world import Params, farm_names, simulate

PARAMS = Params(end_date=date(2026, 1, 31), farms=3, plots_per_farm=(2, 3), years=2, seed=11)


@pytest.fixture(scope="module")
def world():
    return simulate(PARAMS)


def summary(world) -> list:
    """Lo esencial del mundo, comparable entre corridas."""
    return [
        (
            farm.name, farm.management, farm.altitude, len(farm.employees),
            [(p.name, p.variety, p.planting_date, len(p.cycles)) for p in farm.plots],
            [(w.key, round(w.cherry_kg, 6), w.washed_kg, w.delay_h, w.fermentation_h) for w in farm.wets],
            [(d.key, d.start, d.end, d.output_kg, d.destination) for d in farm.dryings],
            [sorted(d.audit.items()) for d in farm.dryings],
        )
        for farm in world.farms
    ]


def test_farm_names_are_unique():
    assert len(set(catalogs.FARM_NAMES)) == len(catalogs.FARM_NAMES)
    many = farm_names(Params(**{**PARAMS.__dict__, "farms": len(catalogs.FARM_NAMES)}))
    assert len(set(many)) == len(catalogs.FARM_NAMES)
    with pytest.raises(ValueError, match="nombres de finca"):
        farm_names(Params(**{**PARAMS.__dict__, "farms": len(catalogs.FARM_NAMES) + 1}))


def test_present_situations_keep_the_world_consistent():
    """Los deslices del presente (dashboards-alertas §4) se aplican sin romper las invariantes."""
    world = simulate(Params(end_date=date(2026, 10, 2)))
    applied = {scenario.split(":")[0] for scenario in world.scenarios}
    assert {"pasada sin cerrar", "finca sin registros", "lavado sin registrar", "secado sin cerrar"} <= applied

    forced = [r for farm in world.farms for r in farm.climate_records if r.forced]
    assert forced and not any(r.recorded for r in forced)
    open_passes = [h for f in world.farms for p in f.plots for c in p.cycles for h in c.harvests if h.end is None]
    assert any((world.params.end_date - h.start).days > 30 for h in open_passes)
    for farm in world.farms:
        for plot in farm.plots:
            assert sum(c.end is None for c in plot.cycles) <= 1
        for drying in farm.dryings:
            assert drying.inputs and all(w.status == "completed" for w, _ in drying.inputs)


def test_same_seed_same_world(world):
    assert summary(simulate(PARAMS)) == summary(world)


def test_another_seed_another_world(world):
    other = simulate(Params(**{**PARAMS.__dict__, "seed": 12}))
    assert summary(other) != summary(world)


def test_missing_level_only_changes_what_is_recorded(world):
    """§3.6 y §7.6: con o sin faltantes, el mundo (y sus targets) es el mismo."""
    complete = simulate(Params(**{**PARAMS.__dict__, "missing_level": "none"}))
    assert summary(complete) == summary(world)
    assert all(recorded for _, _, recorded in complete.registered())
    assert not all(recorded for _, _, recorded in world.registered())


def test_world_produces_the_whole_chain(world):
    dryings = [d for d in world.all_dryings() if d.end is not None]
    assert dryings, "el mundo de prueba debe cerrar secados"
    assert all(d.audit for d in dryings)
    assert all(d.quality.stage == "parchment" for d in dryings if d.quality is not None)


def test_cycles_of_a_plot_do_not_overlap(world):
    for farm in world.farms:
        for plot in farm.plots:
            for previous, current in zip(plot.cycles, plot.cycles[1:]):
                assert previous.end is not None and current.start > previous.end


def test_mass_balance_holds_in_the_world(world):
    for farm in world.farms:
        used = defaultdict(float)
        for wet in farm.wets:
            for harvest, kg in wet.inputs:
                used[id(harvest)] += kg
            if wet.washed_kg is not None:
                assert wet.washed_kg + wet.floats_true <= wet.cherry_kg
        for plot in farm.plots:
            for cycle in plot.cycles:
                for harvest in cycle.harvests:
                    if harvest.total_kg is not None:
                        assert used[id(harvest)] <= harvest.total_kg + 1e-6
        dried = defaultdict(float)
        for drying in farm.dryings:
            for wet, kg in drying.inputs:
                assert wet.status == "completed"
                dried[wet.key] += kg
            if drying.output_kg is not None:
                assert drying.output_kg <= sum(kg for _, kg in drying.inputs)
        for wet in farm.wets:
            assert dried[wet.key] <= (wet.washed_kg or 0) + 1e-6


def test_nobody_picks_two_plots_the_same_day(world):
    for farm in world.farms:
        seen = set()
        for plot in farm.plots:
            for cycle in plot.cycles:
                for harvest in cycle.harvests:
                    for work in harvest.works:
                        key = (work.employee.key, work.day)
                        assert key not in seen
                        seen.add(key)
                        assert work.kg_true <= 200
