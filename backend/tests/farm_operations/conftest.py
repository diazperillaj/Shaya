"""
Fixtures del módulo de cultivo.

Las fixtures que crean recursos lo hacen por la API, con la identidad que
tenga el cliente en ese momento (`login`), así que también ejercitan el
alcance por finca.
"""

import itertools

import pytest

from app.models.farmer import Farmer
from app.models.person import Person
from app.models.user import User
from tests.farm_operations.payloads import API, CYCLE, FARM, PLOT, SUPPLY


@pytest.fixture
def make_farmer(db_session):
    """Caficultor con cuenta: una persona con registro de caficultor y usuario `farmer`."""
    counter = itertools.count(1)

    def _make_farmer(name: str = "Caficultor"):
        n = next(counter)
        person = Person(full_name=f"{name} {n}")
        farmer = Farmer(farm_name="Registro", village="Vereda", municipality="Municipio", person=person)
        user = User(username=f"caficultor_{n}", hashed_password="not-used", role="farmer", person=person)
        db_session.add_all([farmer, user])
        db_session.flush()
        return farmer, user

    return _make_farmer


@pytest.fixture
def admin(make_user):
    return make_user("admin")


@pytest.fixture
def create_farm(client):
    def _create_farm(**overrides) -> dict:
        response = client.post(f"{API}/farms/create", json={**FARM, **overrides})
        assert response.status_code == 200, response.text
        return response.json()

    return _create_farm


@pytest.fixture
def create_plot(client):
    def _create_plot(farm_id: int, **overrides) -> dict:
        response = client.post(f"{API}/plots/create", json={**PLOT, "farm_id": farm_id, **overrides})
        assert response.status_code == 200, response.text
        return response.json()

    return _create_plot


@pytest.fixture
def create_cycle(client):
    def _create_cycle(plot_id: int, **overrides) -> dict:
        response = client.post(f"{API}/crop-cycles/create", json={**CYCLE, "plot_id": plot_id, **overrides})
        assert response.status_code == 200, response.text
        return response.json()

    return _create_cycle


@pytest.fixture
def create_supply(client):
    def _create_supply(**overrides) -> dict:
        response = client.post(f"{API}/supplies/create", json={**SUPPLY, **overrides})
        assert response.status_code == 200, response.text
        return response.json()

    return _create_supply
