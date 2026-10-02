"""
Configuración de alertas en dos niveles: lote → finca → valor por defecto,
con el origen de cada valor.
"""

import pytest

from app.farm_operations.services.alerts import DEFAULTS
from tests.farm_operations.payloads import API


@pytest.fixture
def plot(client, login, make_farmer, create_farm, create_plot):
    _, user = make_farmer()
    login(user)
    farm = create_farm()
    return create_plot(farm["id"])


def values(response):
    return {name: (item["value"], item["source"]) for name, item in response.json()["values"].items()}


def test_without_configuration_everything_comes_from_defaults(client, plot):
    resolved = values(client.get(f"{API}/alert-configs/resolved/plot/{plot['id']}"))

    assert set(resolved) == set(DEFAULTS)
    assert all(source == "default" for _, source in resolved.values())
    assert resolved["irrigation_reminder_days"] == (None, "default"), "el riego viene desactivado"
    assert resolved["broca_alert_pct"] == ("2", "default")


def test_plot_overrides_farm_which_overrides_defaults(client, plot):
    client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={
        "fertilization_reminder_days": 90,
        "max_drying_days": 20,
    })
    client.put(f"{API}/alert-configs/plot/{plot['id']}", json={"max_drying_days": 12})

    resolved = values(client.get(f"{API}/alert-configs/resolved/plot/{plot['id']}"))

    assert resolved["max_drying_days"] == ("12", "plot")
    assert resolved["fertilization_reminder_days"] == ("90", "farm")
    assert resolved["weeding_reminder_days"] == ("75", "default")


def test_removing_the_plot_override_inherits_from_farm_again(client, plot):
    client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={"max_drying_days": 20})
    client.put(f"{API}/alert-configs/plot/{plot['id']}", json={"max_drying_days": 12})

    assert client.delete(f"{API}/alert-configs/plot/{plot['id']}").status_code == 200

    resolved = values(client.get(f"{API}/alert-configs/resolved/plot/{plot['id']}"))
    assert resolved["max_drying_days"] == ("20", "farm")


def test_each_value_carries_what_it_would_inherit(client, plot):
    client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={"max_drying_days": 20})
    client.put(f"{API}/alert-configs/plot/{plot['id']}", json={"max_drying_days": 12})

    plot_value = client.get(f"{API}/alert-configs/resolved/plot/{plot['id']}").json()["values"]["max_drying_days"]
    farm_value = client.get(f"{API}/alert-configs/resolved/farm/{plot['farm_id']}").json()["values"]["max_drying_days"]

    assert (plot_value["inherited_value"], plot_value["inherited_source"]) == ("20", "farm")
    assert (farm_value["inherited_value"], farm_value["inherited_source"]) == ("15", "default")


def test_farm_configuration_shows_its_own_values_and_defaults(client, plot):
    saved = client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={"irrigation_reminder_days": 10})

    resolved = values(saved)
    assert resolved["irrigation_reminder_days"] == ("10", "farm")
    assert resolved["max_drying_days"] == ("15", "default")


def test_all_null_configuration_goes_back_to_defaults(client, plot):
    client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={"max_drying_days": 20})

    client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={})

    resolved = values(client.get(f"{API}/alert-configs/resolved/farm/{plot['farm_id']}"))
    assert all(source == "default" for _, source in resolved.values())


def test_minimum_cannot_exceed_maximum(client, plot):
    response = client.put(
        f"{API}/alert-configs/farm/{plot['farm_id']}",
        json={"min_final_humidity": 13, "max_final_humidity": 11},
    )

    assert response.status_code == 422


def test_other_farmers_configuration_is_not_found(client, login, make_farmer, plot):
    _, intruder = make_farmer()
    login(intruder)

    assert client.get(f"{API}/alert-configs/resolved/plot/{plot['id']}").status_code == 404
    assert client.put(f"{API}/alert-configs/farm/{plot['farm_id']}", json={}).status_code == 404
