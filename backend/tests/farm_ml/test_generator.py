"""
Generador completo contra la base de pruebas (plan-implementacion, bloque 5).

Una generación mínima pasa la validación, es reproducible (misma huella con
la misma semilla) y `--wipe` deja cero filas sintéticas sin tocar las reales.
"""

import sys
from datetime import date
from decimal import Decimal

import pytest

from app.api.api_v1.inventory.schema import ParchmentCreate
from app.api.api_v1.inventory.service import ParchmentService
from app.farm_operations.models import CropCycle, Farm, Fertilization, Plot, Supply
from app.models.farmer import Farmer
from app.models.parchment import Parchment
from app.models.person import Person
from app.models.product import Product, ProductTypeEnum
from scripts.farm_ml import generate_synthetic
from scripts.farm_ml.generate_synthetic import GeneratorError, generate
from scripts.farm_ml.wipe import count_synthetic, wipe_synthetic
from scripts.farm_ml.world import Params

MINIMAL = Params(end_date=date(2026, 1, 31), farms=1, plots_per_farm=(2, 3), years=1, seed=4)


@pytest.fixture
def parchment_product(db_session):
    product = Product(name="Sin tipo", quantity=0, type=ProductTypeEnum.other, active=True, generates_inventory=False)
    db_session.add(product)
    db_session.flush()
    return product


@pytest.fixture
def real_data(db_session, parchment_product):
    """Datos reales que el borrado no debe tocar, incluido un insumo que comparte nombre con el catálogo."""
    person = Person(full_name="Caficultora real")
    farmer = Farmer(person=person, farm_name="Real", village="Vereda", municipality="Municipio")
    farm = Farm(farmer=farmer, name="Finca real", village="Vereda", municipality="Municipio")
    plot = Plot(farm=farm, name="Lote real", variety="Castillo", planting_date=date(2020, 1, 1))
    cycle = CropCycle(plot=plot, cycle_number=1, start_date=date(2025, 1, 1))
    urea = Supply(name="Urea", supply_type="fertilizer", unit="kg")
    db_session.add_all([farm, cycle, urea])
    db_session.flush()
    db_session.add(Fertilization(crop_cycle_id=cycle.id, supply_id=urea.id, application_date=date(2025, 3, 1),
                                 method="soil", quantity=Decimal("50")))
    parchment = ParchmentService(db_session).create_parchment(ParchmentCreate(
        farmer_id=farmer.id, product_id=parchment_product.id, full_price=Decimal("3000000"),
        initial_quantity=Decimal("100"), purchase_date=date(2025, 6, 1),
    ))
    return {"farm": farm.id, "plot": plot.id, "cycle": cycle.id, "supply": urea.id, "parchment": parchment.id}


def test_minimal_generation_passes_validation(db_session, parchment_product):
    result = generate(db_session, MINIMAL)

    assert result.report.passed, [c.detail for c in result.report.errors]
    counts = result.persisted.counts
    for name in ("farms", "plots", "cycles", "harvests", "harvest_works", "wet_processings", "dryings", "parchments"):
        assert counts.get(name, 0) > 0, name
    synthetic = count_synthetic(db_session)
    assert synthetic["farms"] == 1 and synthetic["persons"] == 1
    assert synthetic["dryings"] == counts["dryings"]


def test_same_seed_same_dataset(db_session, parchment_product):
    first = generate(db_session, MINIMAL).fingerprint
    second = generate(db_session, MINIMAL, wipe=True).fingerprint
    other = generate(db_session, Params(**{**MINIMAL.__dict__, "seed": 5}), wipe=True).fingerprint

    assert first == second
    assert other != first


def test_wipe_leaves_no_synthetic_rows_and_keeps_real_ones(db_session, real_data):
    generate(db_session, MINIMAL)
    assert any(count_synthetic(db_session).values())

    wipe_synthetic(db_session)

    assert not any(count_synthetic(db_session).values())
    assert db_session.get(Farm, real_data["farm"]) is not None
    assert db_session.get(Plot, real_data["plot"]) is not None
    assert db_session.get(CropCycle, real_data["cycle"]) is not None
    assert db_session.get(Parchment, real_data["parchment"]) is not None
    # El catálogo de insumos se comparte: el generador reutilizó la urea real y no la borra
    assert db_session.get(Supply, real_data["supply"]) is not None
    assert db_session.query(Supply).filter(Supply.name == "Urea").count() == 1


def test_refuses_to_mix_with_existing_synthetic_data(db_session, parchment_product):
    generate(db_session, MINIMAL)
    with pytest.raises(GeneratorError, match="--wipe"):
        generate(db_session, MINIMAL)


def test_refuses_to_run_in_production(db_session, monkeypatch):
    monkeypatch.setattr(generate_synthetic.settings, "ENV", "production")
    with pytest.raises(GeneratorError, match="producción"):
        generate(db_session, MINIMAL)
    assert not any(count_synthetic(db_session).values())


def test_refuses_more_farms_than_names(db_session):
    from scripts.farm_ml import catalogs

    with pytest.raises(GeneratorError, match="nombres de finca"):
        generate(db_session, Params(**{**MINIMAL.__dict__, "farms": len(catalogs.FARM_NAMES) + 1}))
    assert not any(count_synthetic(db_session).values())


def test_refuses_an_end_date_that_is_not_in_the_past(db_session):
    with pytest.raises(GeneratorError, match="anterior a hoy"):
        generate(db_session, Params(**{**MINIMAL.__dict__, "end_date": date(2999, 1, 1)}))


def test_missing_audit_tools_fail_before_writing(db_session, monkeypatch, tmp_path):
    """Sin pyarrow (imagen que no es la de desarrollo) no se escribe nada en la base."""
    monkeypatch.setitem(sys.modules, "pyarrow", None)
    with pytest.raises(GeneratorError, match="pyarrow"):
        generate(db_session, MINIMAL, output=tmp_path)
    assert not any(count_synthetic(db_session).values())


def test_audit_file_has_one_row_per_closed_drying(db_session, parchment_product, tmp_path):
    import pyarrow.parquet as pq

    result = generate(db_session, MINIMAL, output=tmp_path)

    table = pq.read_table(result.audit_path)
    closed = [d for d in result.world.all_dryings() if d.end is not None]
    assert table.num_rows == len(closed)
    assert {"management", "q_s", "x_bored_pct", "c_fermentation", "noise_score", "target_score"} <= set(table.column_names)
    assert table.schema.metadata[b"seed"] == b"4"
    assert result.report_path.exists()
