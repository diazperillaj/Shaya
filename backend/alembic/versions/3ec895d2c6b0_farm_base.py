"""farm base: supplies, farms, plots, events, alert configs, employees

Primera migración del módulo de cultivo (bloque 1B). Crea las tablas base:
catálogo de insumos, fincas, lotes con su historial de eventos,
configuración de alertas por finca o por lote, y empleados.

- Los tipos enum llevan prefijo `farm` para no chocar con otros módulos.
- `plots` exige fecha de siembra o edad inicial, y fecha de cierre cuando
  está cerrado. Su nombre es único por finca solo entre lotes activos
  (índice parcial): al cerrar un lote y sembrar de nuevo se puede reusar.
- `alert_configs` pertenece a una finca o a un lote, nunca a ambos.
- RESTRICT en la cadena de trazabilidad; CASCADE solo en la configuración
  de alertas, que no tiene valor sin su finca o lote.

Ver app/farm_operations/docs/modelo-datos.md §3.1–3.4, 3.7, 3.9 y
plan-migraciones.md (M1).

Revision ID: 3ec895d2c6b0
Revises: d4a7c9e12f56
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3ec895d2c6b0'
down_revision: Union[str, Sequence[str], None] = 'd4a7c9e12f56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Los tipos se crean y eliminan explícitamente (create_type=False evita que
# create_table intente crearlos de nuevo).
PLOT_STATUS = postgresql.ENUM(
    'active', 'closed',
    name='farmplotstatusenum', create_type=False,
)
PLOT_EVENT_TYPE = postgresql.ENUM(
    'zoca', 'partial_replant', 'shade_change', 'closure', 'reopening', 'other',
    name='farmploteventtypeenum', create_type=False,
)
SUPPLY_TYPE = postgresql.ENUM(
    'fertilizer', 'phytosanitary', 'herbicide', 'amendment', 'other',
    name='farmsupplytypeenum', create_type=False,
)
ENUMS = (PLOT_STATUS, PLOT_EVENT_TYPE, SUPPLY_TYPE)


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
        'supplies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('supply_type', SUPPLY_TYPE, nullable=False),
        sa.Column('other_detail', sa.String(length=150), nullable=True),
        sa.Column('unit', sa.String(length=20), server_default='kg', nullable=False),
        sa.Column('composition', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.true(), nullable=False),
        created_at(),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'supply_type', name='uq_supplies_name_type'),
    )

    op.create_table(
        'farms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farmer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('village', sa.String(length=255), nullable=False),
        sa.Column('municipality', sa.String(length=255), nullable=False),
        sa.Column('altitude', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('total_area', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.ForeignKeyConstraint(['farmer_id'], ['farmers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farmer_id', 'name', name='uq_farms_farmer_name'),
    )
    op.create_index('idx_farm_farmer_id', 'farms', ['farmer_id'])

    op.create_table(
        'plots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', PLOT_STATUS, server_default='active', nullable=False),
        sa.Column('renewed_from_plot_id', sa.Integer(), nullable=True),
        sa.Column('area', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('slope', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('soil_type', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('variety', sa.String(length=100), nullable=False),
        sa.Column('planting_date', sa.Date(), nullable=True),
        sa.Column('initial_age_years', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('seedling_count', sa.Integer(), nullable=True),
        sa.Column('row_spacing_m', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('plant_spacing_m', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('shade_type', sa.String(length=100), nullable=True),
        sa.Column('seed_supplier', sa.String(length=255), nullable=True),
        sa.Column('seed_origin_place', sa.String(length=255), nullable=True),
        sa.Column('seed_purchase_date', sa.Date(), nullable=True),
        sa.Column('seed_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('closed_at', sa.Date(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint(
            'planting_date IS NOT NULL OR initial_age_years IS NOT NULL',
            name='ck_plots_planting_or_age',
        ),
        sa.CheckConstraint(
            "status != 'closed' OR closed_at IS NOT NULL",
            name='ck_plots_closed_has_date',
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['renewed_from_plot_id'], ['plots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_plots_farm_name_active', 'plots', ['farm_id', 'name'],
        unique=True, postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index('idx_plot_farm_id', 'plots', ['farm_id'])
    op.create_index('idx_plot_status', 'plots', ['status'])

    op.create_table(
        'plot_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('plot_id', sa.Integer(), nullable=False),
        sa.Column('event_type', PLOT_EVENT_TYPE, nullable=False),
        sa.Column('other_detail', sa.String(length=150), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        created_at(),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_plot_event_plot_id', 'plot_events', ['plot_id'])
    op.create_index('idx_plot_event_date', 'plot_events', ['event_date'])

    op.create_table(
        'alert_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=True),
        sa.Column('plot_id', sa.Integer(), nullable=True),
        sa.Column('fertilization_reminder_days', sa.Integer(), nullable=True),
        sa.Column('irrigation_reminder_days', sa.Integer(), nullable=True),
        sa.Column('phytosanitary_reminder_days', sa.Integer(), nullable=True),
        sa.Column('weeding_reminder_days', sa.Integer(), nullable=True),
        sa.Column('harvest_reminder_days', sa.Integer(), nullable=True),
        sa.Column('inactivity_alert_days', sa.Integer(), nullable=True),
        sa.Column('max_drying_days', sa.Integer(), nullable=True),
        sa.Column('min_final_humidity', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('max_final_humidity', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('min_fermentation_hours', sa.Integer(), nullable=True),
        sa.Column('max_fermentation_hours', sa.Integer(), nullable=True),
        sa.Column('broca_alert_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        created_at(),
        sa.CheckConstraint(
            '(farm_id IS NULL) != (plot_id IS NULL)',
            name='ck_alert_configs_one_level',
        ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_id'),
        sa.UniqueConstraint('plot_id'),
    )

    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('document', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_employee_farm_id', 'employees', ['farm_id'])


def downgrade() -> None:
    op.drop_index('idx_employee_farm_id', table_name='employees')
    op.drop_table('employees')
    op.drop_table('alert_configs')
    op.drop_index('idx_plot_event_date', table_name='plot_events')
    op.drop_index('idx_plot_event_plot_id', table_name='plot_events')
    op.drop_table('plot_events')
    op.drop_index('idx_plot_status', table_name='plots')
    op.drop_index('idx_plot_farm_id', table_name='plots')
    op.drop_index('uq_plots_farm_name_active', table_name='plots')
    op.drop_table('plots')
    op.drop_index('idx_farm_farmer_id', table_name='farms')
    op.drop_table('farms')
    op.drop_table('supplies')

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind)
