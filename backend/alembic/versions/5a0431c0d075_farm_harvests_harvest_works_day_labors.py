"""farm harvests, harvest works, day labors

Tercera migración del módulo de cultivo (bloque 3). Crea las cosechas (una
sesión por cada pasada de recolección del ciclo), la recolección diaria de
cada empleado y los jornales de las labores que no son recolección.

- Las pasadas de un ciclo se numeran 1, 2, 3… sin repetirse. Una cosecha
  está cerrada si y solo si tiene fecha de fin, y al cerrarse guarda su
  total de café cereza.
- La recolección se paga al peso (kg y tarifa) o por jornal (valor del
  día); el valor a pagar queda almacenado. Pagado ⇔ con fecha de pago.
- La recolección es el detalle de su cosecha (CASCADE); empleados y lotes,
  RESTRICT: son la historia de pagos.

Ver app/farm_operations/docs/modelo-datos.md §3.10–3.12 y
plan-migraciones.md (M3).

Revision ID: 5a0431c0d075
Revises: ef59adecdc0b
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5a0431c0d075'
down_revision: Union[str, Sequence[str], None] = 'ef59adecdc0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Los tipos se crean y eliminan explícitamente (create_type=False evita que
# create_table intente crearlos de nuevo).
HARVEST_STATUS = postgresql.ENUM(
    'open', 'closed',
    name='farmharveststatusenum', create_type=False,
)
HARVEST_PAYMENT_TYPE = postgresql.ENUM(
    'per_kg', 'per_day',
    name='farmharvestpaymenttypeenum', create_type=False,
)
LABOR_ACTIVITY = postgresql.ENUM(
    'weeding', 'pruning', 'fertilization', 'phytosanitary', 'irrigation',
    'shade_regulation', 'maintenance', 'other',
    name='farmlaboractivityenum', create_type=False,
)
ENUMS = (HARVEST_STATUS, HARVEST_PAYMENT_TYPE, LABOR_ACTIVITY)


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
        'harvests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('crop_cycle_id', sa.Integer(), nullable=False),
        sa.Column('pass_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', HARVEST_STATUS, server_default='open', nullable=False),
        sa.Column('rate_per_kg', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('rate_per_day', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_cherry_kg', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint('end_date IS NULL OR end_date >= start_date', name='ck_harvests_dates'),
        sa.CheckConstraint(
            "(status = 'closed') = (end_date IS NOT NULL)",
            name='ck_harvests_end_date_status',
        ),
        sa.CheckConstraint(
            "status != 'closed' OR total_cherry_kg IS NOT NULL",
            name='ck_harvests_closed_total',
        ),
        sa.ForeignKeyConstraint(['crop_cycle_id'], ['crop_cycles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('crop_cycle_id', 'pass_number', name='uq_harvests_cycle_pass'),
    )
    op.create_index('idx_harvest_cycle_id', 'harvests', ['crop_cycle_id'])

    op.create_table(
        'harvest_works',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('harvest_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('payment_type', HARVEST_PAYMENT_TYPE, server_default='per_kg', nullable=False),
        sa.Column('kg_collected', sa.Numeric(precision=10, scale=3), nullable=True),
        sa.Column('rate_per_kg', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('day_value', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('paid', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('paid_at', sa.Date(), nullable=True),
        created_at(),
        sa.CheckConstraint(
            "(payment_type = 'per_kg' AND kg_collected IS NOT NULL AND rate_per_kg IS NOT NULL)"
            " OR (payment_type = 'per_day' AND day_value IS NOT NULL)",
            name='ck_harvest_works_payment',
        ),
        sa.CheckConstraint('paid = (paid_at IS NOT NULL)', name='ck_harvest_works_paid'),
        sa.ForeignKeyConstraint(['harvest_id'], ['harvests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_hwork_harvest_date', 'harvest_works', ['harvest_id', 'work_date'])
    op.create_index('idx_hwork_employee_id', 'harvest_works', ['employee_id'])

    op.create_table(
        'day_labors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('labor_date', sa.Date(), nullable=False),
        sa.Column('activity_type', LABOR_ACTIVITY, nullable=False),
        sa.Column('other_detail', sa.String(length=150), nullable=True),
        sa.Column('plot_id', sa.Integer(), nullable=True),
        sa.Column('daily_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('paid', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('paid_at', sa.Date(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        created_at(),
        sa.CheckConstraint('paid = (paid_at IS NOT NULL)', name='ck_day_labors_paid'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['plot_id'], ['plots.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_day_labor_employee_date', 'day_labors', ['employee_id', 'labor_date'])
    op.create_index('idx_day_labor_plot_id', 'day_labors', ['plot_id'])


def downgrade() -> None:
    op.drop_index('idx_day_labor_plot_id', table_name='day_labors')
    op.drop_index('idx_day_labor_employee_date', table_name='day_labors')
    op.drop_table('day_labors')
    op.drop_index('idx_hwork_employee_id', table_name='harvest_works')
    op.drop_index('idx_hwork_harvest_date', table_name='harvest_works')
    op.drop_table('harvest_works')
    op.drop_index('idx_harvest_cycle_id', table_name='harvests')
    op.drop_table('harvests')

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind)
