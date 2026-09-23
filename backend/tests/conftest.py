"""
Configuración común de las pruebas.

La base es un Postgres efímero y aislado (`docker-compose.test.yml`). Al
iniciar la sesión se construye el esquema completo con `alembic upgrade head`
— así cada corrida valida también la cadena de migraciones — y cada prueba
corre dentro de una transacción que se revierte al terminar.

    docker compose -f docker-compose.test.yml run --rm tests
"""

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db.base import DATABASE_URL
from app.core.db.session import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.person import Person
from app.models.user import User


@pytest.fixture(scope="session")
def engine():
    """Motor de la base de pruebas, con el esquema recién migrado."""

    # Las pruebas borran y reconstruyen el esquema: nunca contra una base real.
    if not settings.DB_NAME.endswith("_test"):
        pytest.exit(
            f"Base de pruebas inválida: {settings.DB_NAME!r} (debe terminar en '_test')"
        )

    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    # Sin archivo .ini: env.py toma la conexión de las variables de entorno y
    # no reconfigura el logging de pytest.
    alembic_config = Config()
    alembic_config.set_main_option("script_location", "alembic")
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    """Sesión dentro de una transacción que se revierte al terminar la prueba.

    Los `commit()` del código bajo prueba cierran solo un savepoint, así que
    nada persiste entre pruebas.
    """

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Cliente HTTP de la app, usando la sesión transaccional de la prueba."""

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    """Crea un usuario con el rol dado.

    La contraseña no se usa: las pruebas se autentican con un token (`login`).
    """

    def _make_user(role: str, username: str | None = None) -> User:
        person = Person(full_name=f"Usuario {role}")
        user = User(
            username=username or f"{role}_test",
            hashed_password="not-used",
            role=role,
            person=person,
        )
        db_session.add(user)
        db_session.flush()
        return user

    return _make_user


@pytest.fixture
def login(client):
    """Autentica el cliente como el usuario dado, con la misma cookie del login real."""

    def _login(user: User) -> TestClient:
        client.cookies.set("access_token", create_access_token({"sub": str(user.id)}))
        return client

    return _login
