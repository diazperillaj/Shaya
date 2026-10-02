"""farm cycles and cycle records

Segunda migración del módulo de cultivo (bloque 2). Crea los ciclos
productivos de los lotes, el clima manual de la finca y las labores del
ciclo: fertilizaciones, aplicaciones fitosanitarias, riegos, monitoreos de
plagas, labores culturales, floraciones y análisis de suelo.

- Un lote tiene a lo sumo un ciclo activo (índice parcial único) y sus
  ciclos se numeran 1, 2, 3… sin repetirse. Un ciclo está cerrado si y solo
  si tiene fecha de fin, que no puede ser anterior a la de inicio.
- Cada labor cuelga de su ciclo; el análisis de suelo, del lote, porque el
  suelo es del terreno. El clima es de la finca, con lote opcional.
- RESTRICT en todas las relaciones: las labores son la historia del ciclo.

Ver app/farm_operations/docs/modelo-datos.md §3.5, 3.6, 3.8 y
plan-migraciones.md (M2).

Revision ID: ef59adecdc0b
Revises: 3ec895d2c6b0
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ef59adecdc0b'
down_revision: Union[str, Sequence[str], None] = '3ec895d2c6b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Los tipos se crean y eliminan explícitamente (create_type=False evita que
# create_table intente crearlos de nuevo).
CYCLE_STATUS = postgresql.ENUM(
    'active', 'closed',
    name='farmcyclestatusenum', create_type=False,
)
FERTILIZATION_METHOD = postgresql.ENUM(
    'soil', 'foliar',
    name='farmfertilizationmethodenum', create_type=False,
)
SEVERITY = postgresql.ENUM(
    'low', 'medium', 'high',
    name='farmseverityenum', create_type=False,
)
INTENSITY = postgresql.ENUM(
    'low', 'medium', 'high',
    name='farmintensityenum', create_type=False,
)
CULTURAL_PRACTICE_TYPE = postgresql.ENUM(
    'weeding', 'pruning', 'shade_regulation', 'amendment', 'other',
    name='farmculturalpracticetypeenum', create_type=False,
)
ENUMS = (CYCLE_STATUS, FERTILIZATION_METHOD, SEVERITY, INTENSITY, CULTURAL_PRACTICE_TYPE)

# (tabla, columna de fecha, índice) de las labores que cuelgan del ciclo
CYCLE_LABOR_INDEXES = (
    ('fertilizations', 'application_date', 'idx_fertilization_cycle_date'),
    ('phytosanitary_apps', 'application_date', 'idx_phytosanitary_cycle_date'),
    ('irrigations', 'irrigation_date', 'idx_irrigation_cycle_date'),
    ('pest_monitorings', 'monitoring_date', 'idx_pest_monitoring_cycle_date'),
    ('cultural_practices', 'practice_date', 'idx_cultural_practice_cycle_date'),
    ('flowering_records', 'flowering_date', 'idx_flowering_cycle_date'),
)


def created_at() -> sa.Column:
    return sa.Column(
        'created_at', sa.DateTime(timezone=True),
        server_default=sa.func.now(), nullable=False,
    )


def labor_table(name: str, *columns) -> None:
    """Crea una labor del ciclo: id, ciclo, columnas propias, observaciones."""
    op.create_table(
        name,
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('crop_cycle_id', sa.Integer(), nullable=False),
        *columns,
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.ForeignKeyConstraint(['crop_cycle_id'], ['crop_cycles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )


def supply_fk() -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(['supply_id'], ['supplies.id'], ondelete='RESTRICT')


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind)

    op.create_table(
        'crop_cycles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('plot_id', sa.Integer(), nullable=False),
        sa.Column('cycle_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', CYCLE_STATUS, server_default='active', nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint(
            'end_date IS NULL OR end_date >= start_date',
            name='ck_crop_cycles_dates',
        ),
        sa.CheckConstraint(
            "(status = 'closed') = (end_date IS NOT NULL)",
            name='ck_crop_cycles_end_date_status',
        ),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plot_id', 'cycle_number', name='uq_crop_cycles_plot_number'),
    )
    op.create_index(
        'uq_crop_cycles_one_active', 'crop_cycles', ['plot_id'],
        unique=True, postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index('idx_crop_cycle_plot_id', 'crop_cycles', ['plot_id'])

    op.create_table(
        'climate_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('plot_id', sa.Integer(), nullable=True),
        sa.Column('record_date', sa.Date(), nullable=False),
        sa.Column('rainfall_mm', sa.Numeric(precision=6, scale=1), nullable=True),
        sa.Column('temp_min_c', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('temp_max_c', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_climate_farm_date', 'climate_records', ['farm_id', 'record_date'])
    op.create_index('idx_climate_plot_id', 'climate_records', ['plot_id'])

    labor_table(
        'fertilizations',
        sa.Column('supply_id', sa.Integer(), nullable=False),
        sa.Column('application_date', sa.Date(), nullable=False),
        sa.Column('method', FERTILIZATION_METHOD, nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('dose_per_tree_g', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('cost', sa.Numeric(precision=12, scale=2), nullable=True),
        supply_fk(),
    )
    labor_table(
        'phytosanitary_apps',
        sa.Column('supply_id', sa.Integer(), nullable=False),
        sa.Column('application_date', sa.Date(), nullable=False),
        sa.Column('target', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('dose_description', sa.String(length=255), nullable=True),
        sa.Column('cost', sa.Numeric(precision=12, scale=2), nullable=True),
        supply_fk(),
    )
    labor_table(
        'irrigations',
        sa.Column('irrigation_date', sa.Date(), nullable=False),
        sa.Column('method', sa.String(length=100), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('volume_liters', sa.Numeric(precision=10, scale=1), nullable=True),
    )
    labor_table(
        'pest_monitorings',
        sa.Column('monitoring_date', sa.Date(), nullable=False),
        sa.Column('broca_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('roya_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('other_pest', sa.String(length=100), nullable=True),
        sa.Column('other_pest_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('severity', SEVERITY, nullable=True),
    )
    labor_table(
        'cultural_practices',
        sa.Column('practice_type', CULTURAL_PRACTICE_TYPE, nullable=False),
        sa.Column('other_detail', sa.String(length=150), nullable=True),
        sa.Column('practice_date', sa.Date(), nullable=False),
        sa.Column('cost', sa.Numeric(precision=12, scale=2), nullable=True),
    )
    labor_table(
        'flowering_records',
        sa.Column('flowering_date', sa.Date(), nullable=False),
        sa.Column('intensity', INTENSITY, nullable=False),
    )
    for table, date_column, index in CYCLE_LABOR_INDEXES:
        op.create_index(index, table, ['crop_cycle_id', date_column])

    op.create_table(
        'soil_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('plot_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.Date(), nullable=False),
        sa.Column('ph', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('organic_matter_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('nitrogen', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('phosphorus', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('potassium', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('texture', sa.String(length=100), nullable=True),
        sa.Column('laboratory', sa.String(length=150), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_soil_analysis_plot_date', 'soil_analyses', ['plot_id', 'analysis_date'])


def downgrade() -> None:
    op.drop_index('idx_soil_analysis_plot_date', table_name='soil_analyses')
    op.drop_table('soil_analyses')
    for table, _, index in reversed(CYCLE_LABOR_INDEXES):
        op.drop_index(index, table_name=table)
        op.drop_table(table)
    op.drop_index('idx_climate_plot_id', table_name='climate_records')
    op.drop_index('idx_climate_farm_date', table_name='climate_records')
    op.drop_table('climate_records')
    op.drop_index('idx_crop_cycle_plot_id', table_name='crop_cycles')
    op.drop_index('uq_crop_cycles_one_active', table_name='crop_cycles')
    op.drop_table('crop_cycles')

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind)
