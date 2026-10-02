"""
Lotes: siembra o edad obligatoria, nombre único entre lotes activos, cierre
definitivo, reapertura solo para corregir un error, renovación del terreno
y eventos del historial.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.farm_operations.api.v1.plots.service import effective_age_years
from app.farm_operations.models import Plot
from app.farm_operations.services import dates
from app.farm_operations.services.dates import business_today
from tests.farm_operations.payloads import API, PLOT


@pytest.fixture
def farm(client, login, make_farmer, create_farm):
    """Finca de un caficultor con la sesión de ese caficultor abierta."""
    _, user = make_farmer()
    login(user)
    return create_farm()


def error_messages(response):
    detail = response.json()["detail"]
    return detail if isinstance(detail, str) else " ".join(e["msg"] for e in detail)


# ── Siembra ──────────────────────────────────────────────────────────────


def test_plot_needs_planting_date_or_age(client, farm):
    response = client.post(
        f"{API}/plots/create",
        json={"name": "Lote 1", "variety": "Castillo", "farm_id": farm["id"]},
    )

    assert response.status_code == 422
    assert "fecha de siembra o la edad" in error_messages(response)


def test_established_plot_registers_with_its_age(client, farm, create_plot):
    plot = create_plot(farm["id"], planting_date=None, initial_age_years="6.5")

    assert Decimal(plot["effective_age_years"]) == Decimal("6.5")


def test_database_rejects_plot_without_planting_date_or_age(db_session, farm):
    db_session.add(Plot(farm_id=farm["id"], name="Sin datos", variety="Caturra"))

    with pytest.raises(IntegrityError, match="ck_plots_planting_or_age"):
        db_session.flush()


# ── Nombre único entre lotes activos ─────────────────────────────────────


def test_active_plot_names_are_unique_per_farm(client, farm, create_plot):
    create_plot(farm["id"])

    duplicate = client.post(f"{API}/plots/create", json={**PLOT, "name": "lote 1", "farm_id": farm["id"]})

    assert duplicate.status_code == 409


def test_name_is_reusable_after_closing_the_plot(client, farm, create_plot):
    old = create_plot(farm["id"])
    client.post(f"{API}/plots/{old['id']}/close", json={})

    new = create_plot(farm["id"], renewed_from_plot_id=old["id"])

    assert new["name"] == old["name"]


# ── Cierre y reapertura ──────────────────────────────────────────────────


def test_close_is_recorded_as_an_event(client, farm, create_plot):
    plot = create_plot(farm["id"])

    closed = client.post(f"{API}/plots/{plot['id']}/close", json={"description": "Dejó de producir"})

    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert closed.json()["closed_at"] == business_today().isoformat()
    events = client.get(f"{API}/plots/{plot['id']}/events/get").json()
    assert [(e["event_type"], e["description"]) for e in events] == [("closure", "Dejó de producir")]
    assert client.post(f"{API}/plots/{plot['id']}/close", json={}).status_code == 409


def test_reopen_corrects_a_mistaken_close(client, farm, create_plot):
    plot = create_plot(farm["id"])
    client.post(f"{API}/plots/{plot['id']}/close", json={})

    reopened = client.post(f"{API}/plots/{plot['id']}/reopen", json={"description": "Cerrado por error"})

    assert reopened.status_code == 200
    assert reopened.json()["status"] == "active"
    assert reopened.json()["closed_at"] is None
    types = [e["event_type"] for e in client.get(f"{API}/plots/{plot['id']}/events/get").json()]
    assert sorted(types) == ["closure", "reopening"]


def test_dates_set_by_the_server_follow_the_colombian_calendar(client, farm, create_plot, monkeypatch):
    # 8 p. m. del 28 de febrero en Colombia: en UTC ya es 1 de marzo
    evening = datetime(2025, 3, 1, 1, 0, tzinfo=timezone.utc)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return evening.astimezone(tz)

    monkeypatch.setattr(dates, "datetime", FrozenDatetime)
    plot = create_plot(farm["id"])

    closed = client.post(f"{API}/plots/{plot['id']}/close", json={})
    client.post(f"{API}/plots/{plot['id']}/reopen", json={})

    assert closed.json()["closed_at"] == "2025-02-28"
    events = client.get(f"{API}/plots/{plot['id']}/events/get").json()
    assert [e["event_date"] for e in events] == ["2025-02-28", "2025-02-28"]


def test_renewed_plot_cannot_be_reopened(client, farm, create_plot):
    old = create_plot(farm["id"])
    client.post(f"{API}/plots/{old['id']}/close", json={})
    create_plot(farm["id"], name="Lote nuevo", renewed_from_plot_id=old["id"])

    response = client.post(f"{API}/plots/{old['id']}/reopen", json={})

    assert response.status_code == 409
    assert "Lote nuevo" in response.json()["detail"]


def test_reopen_clashes_with_active_plot_of_same_name(client, farm, create_plot):
    old = create_plot(farm["id"])
    client.post(f"{API}/plots/{old['id']}/close", json={})
    create_plot(farm["id"])  # mismo nombre, sin ser renovación

    assert client.post(f"{API}/plots/{old['id']}/reopen", json={}).status_code == 409


# ── Renovación ───────────────────────────────────────────────────────────


def test_renewal_reuses_the_terrain_of_a_closed_plot(client, farm, create_plot):
    old = create_plot(farm["id"], area="2.5", slope="30", soil_type="Franco", location="Ladera norte")
    client.post(f"{API}/plots/{old['id']}/close", json={})

    defaults = client.get(f"{API}/plots/get/{old['id']}/renewal-defaults").json()
    assert defaults == {
        "farm_id": farm["id"],
        "renewed_from_plot_id": old["id"],
        "name": "Lote 1",
        "area": "2.50",
        "slope": "30.00",
        "soil_type": "Franco",
        "location": "Ladera norte",
    }

    new = create_plot(farm["id"], renewed_from_plot_id=old["id"], variety="Cenicafé 1", planting_date="2025-02-01")
    assert new["renewed_from_plot_id"] == old["id"]
    assert client.get(f"{API}/plots/get/{old['id']}").json()["renewed_by_plot_id"] == new["id"]


def test_renewal_rules(client, login, farm, create_farm, create_plot):
    active = create_plot(farm["id"])
    assert (
        client.post(f"{API}/plots/create", json={**PLOT, "name": "Otro", "farm_id": farm["id"], "renewed_from_plot_id": active["id"]}).status_code
        == 409
    ), "solo se renueva un lote cerrado"

    client.post(f"{API}/plots/{active['id']}/close", json={})
    other_farm = create_farm(name="Otra finca")
    assert (
        client.post(f"{API}/plots/create", json={**PLOT, "farm_id": other_farm["id"], "renewed_from_plot_id": active["id"]}).status_code
        == 409
    ), "la renovación es en la misma finca"

    create_plot(farm["id"], renewed_from_plot_id=active["id"])
    assert (
        client.post(f"{API}/plots/create", json={**PLOT, "name": "Otra vez", "farm_id": farm["id"], "renewed_from_plot_id": active["id"]}).status_code
        == 409
    ), "un lote se renueva una sola vez"


# ── Eventos y edad efectiva ──────────────────────────────────────────────


def test_zoca_restarts_the_effective_age(client, farm, create_plot):
    plot = create_plot(farm["id"], planting_date="2015-01-01")
    one_year_ago = (business_today() - timedelta(days=365)).isoformat()

    event = client.post(f"{API}/plots/{plot['id']}/events/create", json={"event_type": "zoca", "event_date": one_year_ago})

    assert event.status_code == 200
    detail = client.get(f"{API}/plots/get/{plot['id']}").json()
    assert detail["last_zoca_date"] == one_year_ago
    assert Decimal(detail["effective_age_years"]) == Decimal("1.0")


@pytest.mark.parametrize(
    "payload, problem",
    [
        ({"event_type": "closure"}, "propias acciones"),
        ({"event_type": "reopening"}, "propias acciones"),
        ({"event_type": "other"}, "cuál evento"),
        ({"event_type": "zoca", "event_date": "2999-01-01"}, "futura"),
    ],
)
def test_invalid_events_are_rejected(client, farm, create_plot, payload, problem):
    plot = create_plot(farm["id"])

    response = client.post(f"{API}/plots/{plot['id']}/events/create", json={"event_date": "2024-01-01", **payload})

    assert response.status_code == 422
    assert problem in error_messages(response)


def test_closed_plot_takes_no_new_events(client, farm, create_plot):
    plot = create_plot(farm["id"])
    client.post(f"{API}/plots/{plot['id']}/close", json={})

    response = client.post(
        f"{API}/plots/{plot['id']}/events/create",
        json={"event_type": "other", "other_detail": "Poda", "event_date": "2024-01-01"},
    )

    assert response.status_code == 409


def plot_stub(**fields):
    defaults = {"planting_date": None, "initial_age_years": None, "closed_at": None,
                "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc)}
    return SimpleNamespace(**{**defaults, **fields})


@pytest.mark.parametrize(
    "plot, last_zoca, expected",
    [
        (plot_stub(planting_date=date(2022, 1, 1)), None, Decimal("3.0")),
        (plot_stub(initial_age_years=Decimal("5.0")), None, Decimal("6.0")),
        (plot_stub(planting_date=date(2010, 1, 1)), date(2024, 1, 1), Decimal("1.0")),
        # Al cierre la edad queda congelada
        (plot_stub(planting_date=date(2020, 1, 1), closed_at=date(2023, 1, 1)), None, Decimal("3.0")),
    ],
)
def test_effective_age(plot, last_zoca, expected):
    assert effective_age_years(plot, last_zoca, today=date(2025, 1, 1)) == expected


def test_registration_day_is_the_colombian_one():
    # Registrado a las 8 p. m. del 31 de diciembre en Colombia (1 de enero en UTC):
    # 19 días después suman 0,1 años; contando desde el 1 de enero serían 18 (0,0)
    plot = plot_stub(initial_age_years=Decimal("2.0"), created_at=datetime(2025, 1, 1, 1, 0, tzinfo=timezone.utc))

    assert effective_age_years(plot, None, today=date(2025, 1, 19)) == Decimal("2.1")


# ── Borrado y alcance ────────────────────────────────────────────────────


def test_only_plots_without_history_can_be_deleted(client, farm, create_plot):
    fresh = create_plot(farm["id"])
    with_history = create_plot(farm["id"], name="Lote 2")
    client.post(
        f"{API}/plots/{with_history['id']}/events/create",
        json={"event_type": "shade_change", "event_date": "2024-01-01"},
    )

    assert client.delete(f"{API}/plots/delete/{with_history['id']}").status_code == 409
    assert client.delete(f"{API}/plots/delete/{fresh['id']}").status_code == 200


def test_other_farmers_plot_is_not_found(client, login, make_farmer, farm, create_plot):
    plot = create_plot(farm["id"])
    _, intruder = make_farmer()
    login(intruder)

    assert client.get(f"{API}/plots/get/{plot['id']}").status_code == 404
    assert client.post(f"{API}/plots/{plot['id']}/close", json={}).status_code == 404
    assert client.get(f"{API}/plots/get", params={"farm_id": farm["id"]}).json() == []
    assert client.post(f"{API}/plots/create", json={**PLOT, "farm_id": farm["id"]}).status_code == 404
