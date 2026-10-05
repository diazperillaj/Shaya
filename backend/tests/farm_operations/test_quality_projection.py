"""
Proyección de calidad (generador-sintetico-ml §6, especificacion-api §3.14).

Usa el artefacto versionado del repositorio: la prueba de humo compara lo
que responde la API con lo que da el artefacto cargado a mano (§7.7).
"""

from datetime import date

import joblib
import numpy as np
import pytest

from app.farm_operations.ml import predictor
from app.farm_operations.ml.features import build_features, cycle_origins, fill_future_stages, to_matrix
from app.farm_operations.models import CropCycle, Plot
from app.farm_operations.services.dates import business_today
from tests.farm_ml.blend import build_blend
from tests.farm_operations.payloads import API


@pytest.fixture(autouse=True)
def fresh_model():
    predictor.reset_model()
    yield
    predictor.reset_model()


def new_plot(db, farm, name="C", cycle=True) -> Plot:
    """Un lote recién sembrado, con su ciclo activo y sin nada cosechado."""
    plot = Plot(farm=farm, name=name, variety="Geisha", planting_date=date(2022, 3, 1))
    db.add(CropCycle(plot=plot, cycle_number=1, start_date=date(2026, 1, 1)) if cycle else plot)
    db.flush()
    return plot


def test_plot_with_a_closed_drying_gets_the_three_values(db_session, login, admin):
    blend = build_blend(db_session)
    response = login(admin).get(f"{API}/plots/{blend['plot_a'].id}/quality-projection")

    assert response.status_code == 200
    body = response.json()
    assert body["crop_cycle_id"] == blend["cycle_a"].id and body["plot_name"] == "A"
    assert body["stages"] == ["pre", "harvest", "wet", "drying"] and body["completeness"] == 1.0
    assert 60 < body["score"] < 95 and 0 <= body["defects_pct"] < 30 and 80 < body["yield_factor"] < 120
    assert "humidity_pct" not in body   # la humedad no se predice: se mide al cerrar el secado
    assert body["model_version"] == "v1" and "sintéticos" in body["disclaimer"]


def test_a_cycle_without_harvest_is_projected_from_its_farm(db_session, login, admin):
    """Sin cosecha ni proceso, las etapas futuras salen de los valores típicos de la finca."""
    blend = build_blend(db_session)
    plot = new_plot(db_session, blend["farm"])

    body = login(admin).get(f"{API}/plots/{plot.id}/quality-projection").json()
    assert body["stages"] == ["pre"]
    assert body["score"] is not None and body["completeness"] < 1.0


def test_future_stages_take_the_typical_values_of_the_farm(db_session):
    """El relleno de un ciclo sin beneficio ni secado sale de los secados cerrados de su finca."""
    blend = build_blend(db_session)
    reference = predictor.farm_references(db_session, [blend["farm"].id], business_today())[blend["farm"].id]
    assert reference["fermentation_hours"] == pytest.approx((16 * 100 + 24 * 200) / 300)
    assert reference["drying_method"] == "marquesina"


def test_serving_matches_the_artifact(db_session, login, admin):
    """Prueba de humo (§7.7): la API predice lo mismo que el artefacto cargado a mano."""
    blend = build_blend(db_session)
    plot = new_plot(db_session, blend["farm"])
    body = login(admin).get(f"{API}/plots/{plot.id}/quality-projection").json()

    bundle = joblib.load(predictor.ARTIFACT)
    [row] = build_features(db_session, cycle_origins(db_session, [body["crop_cycle_id"]], business_today()))
    reference = predictor.farm_references(db_session, [blend["farm"].id], business_today())[blend["farm"].id]
    values = fill_future_stages(row.values, row.stages, reference, bundle["global_reference"])
    matrix = to_matrix([values], bundle["vocabularies"])
    for target in ("score", "defects_pct", "yield_factor"):
        expected = float(bundle["models"][target].predict(matrix)[0])
        assert body[target] == pytest.approx(round(expected, 1))
    assert np.isfinite(matrix).sum() > 20   # la fila llegó con datos, no vacía


def test_plot_without_an_active_cycle_is_a_conflict(db_session, login, admin):
    blend = build_blend(db_session)
    plot = new_plot(db_session, blend["farm"], name="Sin ciclo", cycle=False)
    response = login(admin).get(f"{API}/plots/{plot.id}/quality-projection")
    assert response.status_code == 409 and "ciclo activo" in response.json()["detail"]


def test_dashboard_lists_the_active_cycles_of_the_scope(db_session, login, admin, make_farmer):
    farmer, user = make_farmer()
    mine = build_blend(db_session, farmer=farmer, name="Mi finca")
    other = build_blend(db_session, name="Ajena")
    new_plot(db_session, mine["farm"])

    client = login(user)
    rows = client.get(f"{API}/dashboard/quality-projections").json()
    assert [(r["farm_name"], r["plot_name"]) for r in rows] == [("Mi finca", "A"), ("Mi finca", "B"), ("Mi finca", "C")]
    assert [r["stages"][-1] for r in rows] == ["drying", "drying", "pre"]
    assert client.get(f"{API}/dashboard/quality-projections?farm_id={other['farm'].id}").status_code == 404
    assert client.get(f"{API}/plots/{other['plot_a'].id}/quality-projection").status_code == 404

    everything = login(admin).get(f"{API}/dashboard/quality-projections").json()
    assert {r["farm_name"] for r in everything} == {"Mi finca", "Ajena"}


def test_without_a_model_the_projection_is_unavailable(db_session, login, admin, monkeypatch, tmp_path):
    blend = build_blend(db_session)
    monkeypatch.setattr(predictor, "ARTIFACT", tmp_path / "missing.joblib")
    response = login(admin).get(f"{API}/plots/{blend['plot_a'].id}/quality-projection")
    assert response.status_code == 503 and "no está disponible" in response.json()["detail"]


def test_a_model_trained_with_other_versions_is_refused(db_session, login, admin, monkeypatch, tmp_path):
    blend = build_blend(db_session)
    path = tmp_path / "old.joblib"
    joblib.dump({"sklearn_version": "0.0.1", "numpy_version": "0.0.1", "features": []}, path)
    monkeypatch.setattr(predictor, "ARTIFACT", path)
    response = login(admin).get(f"{API}/plots/{blend['plot_a'].id}/quality-projection")
    assert response.status_code == 503 and "scikit-learn 0.0.1" in response.json()["detail"]
