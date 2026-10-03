"""farm wet processing, drying, quality evals

Cuarta migración del módulo de cultivo (bloque 4). Crea el beneficio
húmedo y el secado, con sus pivotes (las mezclas: varias cosechas en un
beneficio, varios beneficios en un secado, con los kg que aporta cada uno),
las mediciones de humedad del secado y las evaluaciones de calidad.

- Los pivotes exigen kg positivos y no repiten el mismo origen; son el
  detalle de su cabecera (CASCADE) y protegen su origen (RESTRICT).
- Un beneficio completado tiene su café lavado; la fermentación termina
  después de empezar. Un secado completado tiene fin, pergamino seco,
  humedad final y destino.
- Una evaluación de calidad es de una cosecha (en cereza) o de un secado
  (en pergamino), nunca de ambos; porcentajes y puntaje entre 0 y 100.

Ver app/farm_operations/docs/modelo-datos.md §3.13–3.17 y
plan-migraciones.md (M4).

Revision ID: 9a5de8974e57
Revises: 5a0431c0d075
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9a5de8974e57'
down_revision: Union[str, Sequence[str], None] = '5a0431c0d075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Los tipos se crean y eliminan explícitamente (create_type=False evita que
# create_table intente crearlos de nuevo).
WET_PROCESSING_STATUS = postgresql.ENUM(
    'in_progress', 'completed', name='farmwetprocessingstatusenum', create_type=False,
)
FERMENTATION_METHOD = postgresql.ENUM(
    'tank', 'dry', 'water', 'other', name='farmfermentationmethodenum', create_type=False,
)
DRYING_STATUS = postgresql.ENUM(
    'in_progress', 'completed', name='farmdryingstatusenum', create_type=False,
)
DRYING_METHOD = postgresql.ENUM(
    'elba', 'marquesina', 'patio', 'mechanical_silo', 'other', name='farmdryingmethodenum', create_type=False,
)
DRYING_DESTINATION = postgresql.ENUM(
    'inventory', 'direct_sale', 'stored', name='farmdryingdestinationenum', create_type=False,
)
QUALITY_STAGE = postgresql.ENUM(
    'cherry', 'parchment', name='farmqualitystageenum', create_type=False,
)
ENUMS = (
    WET_PROCESSING_STATUS, FERMENTATION_METHOD, DRYING_STATUS,
    DRYING_METHOD, DRYING_DESTINATION, QUALITY_STAGE,
)

PERCENT_COLUMNS = ('ripe_pct', 'green_pct', 'overripe_pct', 'bored_pct', 'humidity_pct', 'defects_pct', 'score')


def created_at() -> sa.Column:
    return sa.Column(
        'created_at', sa.DateTime(timezone=True),
        server_default=sa.func.now(), nullable=False,
    )


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind)

    op.create_table(
        'wet_processings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('status', WET_PROCESSING_STATUS, server_default='in_progress', nullable=False),
        sa.Column('floats_kg', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('floats_method', sa.String(length=100), nullable=True),
        sa.Column('pulped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fermentation_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fermentation_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fermentation_method', FERMENTATION_METHOD, nullable=True),
        sa.Column('fermentation_other_detail', sa.String(length=150), nullable=True),
        sa.Column('fermentation_decided_by', sa.String(length=150), nullable=True),
        sa.Column('fermentation_criteria', sa.String(length=255), nullable=True),
        sa.Column('ambient_temp_c', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('wash_count', sa.Integer(), nullable=True),
        sa.Column('washed_kg', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint(
            'fermentation_end IS NULL OR (fermentation_start IS NOT NULL AND fermentation_end >= fermentation_start)',
            name='ck_wet_processings_fermentation',
        ),
        sa.CheckConstraint(
            "status != 'completed' OR washed_kg IS NOT NULL",
            name='ck_wet_processings_completed',
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_wet_processing_farm_id', 'wet_processings', ['farm_id'])

    op.create_table(
        'wet_processing_inputs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wet_processing_id', sa.Integer(), nullable=False),
        sa.Column('harvest_id', sa.Integer(), nullable=False),
        sa.Column('cherry_kg', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.CheckConstraint('cherry_kg > 0', name='ck_wet_processing_inputs_kg'),
        sa.ForeignKeyConstraint(['wet_processing_id'], ['wet_processings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['harvest_id'], ['harvests.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('wet_processing_id', 'harvest_id', name='uq_wet_processing_inputs_harvest'),
    )
    op.create_index('idx_wp_input_harvest_id', 'wet_processing_inputs', ['harvest_id'])

    op.create_table(
        'dryings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('status', DRYING_STATUS, server_default='in_progress', nullable=False),
        sa.Column('method', DRYING_METHOD, nullable=False),
        sa.Column('other_detail', sa.String(length=150), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('final_humidity_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('output_kg', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('packaging', sa.String(length=150), nullable=True),
        sa.Column('sack_count', sa.Integer(), nullable=True),
        sa.Column('packed_at', sa.Date(), nullable=True),
        sa.Column('storage_place', sa.String(length=150), nullable=True),
        sa.Column('destination', DRYING_DESTINATION, nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_dryings_dates'),
        sa.CheckConstraint("(status = 'completed') = (end_date IS NOT NULL)", name='ck_dryings_end_date_status'),
        sa.CheckConstraint(
            "status != 'completed' OR (output_kg IS NOT NULL AND final_humidity_pct IS NOT NULL"
            " AND destination IS NOT NULL)",
            name='ck_dryings_completed_fields',
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_drying_farm_id', 'dryings', ['farm_id'])

    op.create_table(
        'drying_inputs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drying_id', sa.Integer(), nullable=False),
        sa.Column('wet_processing_id', sa.Integer(), nullable=False),
        sa.Column('wet_kg', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.CheckConstraint('wet_kg > 0', name='ck_drying_inputs_kg'),
        sa.ForeignKeyConstraint(['drying_id'], ['dryings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['wet_processing_id'], ['wet_processings.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('drying_id', 'wet_processing_id', name='uq_drying_inputs_wet_processing'),
    )
    op.create_index('idx_drying_input_wet_processing_id', 'drying_inputs', ['wet_processing_id'])

    op.create_table(
        'drying_humidity_checks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('drying_id', sa.Integer(), nullable=False),
        sa.Column('check_date', sa.Date(), nullable=False),
        sa.Column('humidity_pct', sa.Numeric(precision=5, scale=2), nullable=False),
        created_at(),
        sa.CheckConstraint('humidity_pct >= 0 AND humidity_pct <= 100', name='ck_drying_humidity_checks_range'),
        sa.ForeignKeyConstraint(['drying_id'], ['dryings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_humidity_check_drying_id', 'drying_humidity_checks', ['drying_id'])

    op.create_table(
        'quality_evals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stage', QUALITY_STAGE, nullable=False),
        sa.Column('harvest_id', sa.Integer(), nullable=True),
        sa.Column('drying_id', sa.Integer(), nullable=True),
        sa.Column('eval_date', sa.Date(), nullable=False),
        sa.Column('ripe_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('green_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('overripe_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('bored_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('humidity_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('defects_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('yield_factor', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint(
            "(stage = 'cherry' AND harvest_id IS NOT NULL AND drying_id IS NULL)"
            " OR (stage = 'parchment' AND drying_id IS NOT NULL AND harvest_id IS NULL)",
            name='ck_quality_evals_stage_ref',
        ),
        sa.CheckConstraint(
            ' AND '.join(f'({column} IS NULL OR ({column} >= 0 AND {column} <= 100))' for column in PERCENT_COLUMNS),
            name='ck_quality_evals_ranges',
        ),
        sa.ForeignKeyConstraint(['harvest_id'], ['harvests.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['drying_id'], ['dryings.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_quality_eval_harvest_id', 'quality_evals', ['harvest_id'])
    op.create_index('idx_quality_eval_drying_id', 'quality_evals', ['drying_id'])


def downgrade() -> None:
    op.drop_index('idx_quality_eval_drying_id', table_name='quality_evals')
    op.drop_index('idx_quality_eval_harvest_id', table_name='quality_evals')
    op.drop_table('quality_evals')
    op.drop_index('idx_humidity_check_drying_id', table_name='drying_humidity_checks')
    op.drop_table('drying_humidity_checks')
    op.drop_index('idx_drying_input_wet_processing_id', table_name='drying_inputs')
    op.drop_table('drying_inputs')
    op.drop_index('idx_drying_farm_id', table_name='dryings')
    op.drop_table('dryings')
    op.drop_index('idx_wp_input_harvest_id', table_name='wet_processing_inputs')
    op.drop_table('wet_processing_inputs')
    op.drop_index('idx_wet_processing_farm_id', table_name='wet_processings')
    op.drop_table('wet_processings')

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind)
