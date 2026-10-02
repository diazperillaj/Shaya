"""
Clima manual (de la finca, con lote opcional) y análisis de suelo (del lote).
"""

import pytest

from tests.farm_operations.payloads import API

RAIN = {"record_date": "2025-03-01", "rainfall_mm": "12.5"}
SOIL = {"analysis_date": "2025-02-01", "ph": "5.2", "organic_matter_pct": "8.5", "laboratory": "Agrosavia"}


@pytest.fixture
def farm(client, login, make_farmer, create_farm):
    _, user = make_farmer()
    login(user)
    return create_farm()


@pytest.fixture
def plot(farm, create_plot):
    return create_plot(farm["id"])


# ── Clima ────────────────────────────────────────────────────────────────


def test_climate_belongs_to_the_farm_or_one_plot(client, farm, plot):
    whole_farm = client.post(f"{API}/climate-records/create", json={**RAIN, "farm_id": farm["id"]})
    one_plot = client.post(f"{API}/climate-records/create", json={
        **RAIN, "farm_id": farm["id"], "plot_id": plot["id"], "temp_min_c": "14", "temp_max_c": "26",
    })

    assert (whole_farm.status_code, one_plot.status_code) == (200, 200)
    assert whole_farm.json()["plot_name"] is None
    assert one_plot.json()["plot_name"] == plot["name"]
    listed = client.get(f"{API}/climate-records/get", params={"farm_id": farm["id"]}).json()
    assert len(listed) == 2


@pytest.mark.parametrize(
    "body, problem",
    [
        ({"record_date": "2025-03-01"}, "lluvia, la temperatura o una observación"),
        ({**RAIN, "temp_min_c": "28", "temp_max_c": "20"}, "mínima no puede ser mayor"),
        ({**RAIN, "record_date": "2999-01-01"}, "no puede ser futura"),
    ],
)
def test_invalid_climate_is_rejected(client, farm, body, problem):
    response = client.post(f"{API}/climate-records/create", json={**body, "farm_id": farm["id"]})

    assert response.status_code == 422
    assert problem in " ".join(error["msg"] for error in response.json()["detail"])


def test_climate_plot_must_be_of_the_same_farm(client, farm, create_farm, create_plot):
    other_plot = create_plot(create_farm(name="Otra finca")["id"])

    response = client.post(f"{API}/climate-records/create", json={
        **RAIN, "farm_id": farm["id"], "plot_id": other_plot["id"],
    })

    assert response.status_code == 409


def test_climate_record_is_corrected_and_deleted(client, farm, plot):
    record = client.post(f"{API}/climate-records/create", json={**RAIN, "farm_id": farm["id"]}).json()

    updated = client.put(f"{API}/climate-records/update/{record['id']}", json={
        **RAIN, "rainfall_mm": "20", "plot_id": plot["id"],
    })
    assert updated.status_code == 200
    assert (updated.json()["rainfall_mm"], updated.json()["plot_id"]) == ("20.0", plot["id"])

    assert client.delete(f"{API}/climate-records/delete/{record['id']}").status_code == 200


def test_farm_with_climate_records_is_not_deleted(client, farm):
    client.post(f"{API}/climate-records/create", json={**RAIN, "farm_id": farm["id"]})

    assert client.delete(f"{API}/farms/delete/{farm['id']}").status_code == 409


def test_climate_of_other_farms_is_out_of_reach(client, login, make_farmer, farm):
    record = client.post(f"{API}/climate-records/create", json={**RAIN, "farm_id": farm["id"]}).json()
    _, intruder = make_farmer("Otro")
    login(intruder)

    assert client.get(f"{API}/climate-records/get").json() == []
    assert client.post(f"{API}/climate-records/create", json={**RAIN, "farm_id": farm["id"]}).status_code == 404
    assert client.delete(f"{API}/climate-records/delete/{record['id']}").status_code == 404


# ── Análisis de suelo ────────────────────────────────────────────────────


def test_soil_analysis_hangs_from_the_plot(client, plot):
    created = client.post(f"{API}/soil-analyses/create", json={**SOIL, "plot_id": plot["id"]})

    assert created.status_code == 200
    assert created.json()["plot_name"] == plot["name"]
    assert len(client.get(f"{API}/soil-analyses/get", params={"plot_id": plot["id"]}).json()) == 1

    record_id = created.json()["id"]
    updated = client.put(f"{API}/soil-analyses/update/{record_id}", json={**SOIL, "ph": "5.6"})
    assert updated.json()["ph"] == "5.60"
    assert client.delete(f"{API}/soil-analyses/delete/{record_id}").status_code == 200


def test_soil_analysis_needs_a_result(client, plot):
    response = client.post(f"{API}/soil-analyses/create", json={
        "plot_id": plot["id"], "analysis_date": "2025-02-01", "laboratory": "Agrosavia", "texture": "  ",
    })

    assert response.status_code == 422


def test_closed_plot_takes_no_soil_analyses(client, plot):
    client.post(f"{API}/plots/{plot['id']}/close", json={})

    assert client.post(f"{API}/soil-analyses/create", json={**SOIL, "plot_id": plot["id"]}).status_code == 409


def test_plot_with_soil_analyses_is_not_deleted(client, plot):
    client.post(f"{API}/soil-analyses/create", json={**SOIL, "plot_id": plot["id"]})

    assert client.delete(f"{API}/plots/delete/{plot['id']}").status_code == 409
