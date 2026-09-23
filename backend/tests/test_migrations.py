"""
La cadena de migraciones construye el esquema completo y coincide con los
modelos: si un modelo cambia sin su migración (o al revés), estas pruebas
fallan.
"""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.core.db.base import Base


def test_migrations_create_every_model_table(engine):
    tables = set(inspect(engine).get_table_names())

    assert set(Base.metadata.tables) <= tables


def test_models_match_migrated_schema(engine):
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)

    assert diff == []
