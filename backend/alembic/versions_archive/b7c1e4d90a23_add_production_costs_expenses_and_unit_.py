"""add production costs: process/product expenses and unit_cost

Revision ID: b7c1e4d90a23
Revises: 4fbb6037b8df
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c1e4d90a23'
down_revision: Union[str, Sequence[str], None] = '4fbb6037b8df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Gastos adicionales por proceso (transporte, mano de obra, etc.)
    op.create_table(
        'process_expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column(
            'category',
            sa.Enum('transport', 'labor', 'supplies', 'other', name='processexpensecategoryenum'),
            nullable=False,
        ),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['process_id'], ['processes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_process_expense_process_id', 'process_expenses', ['process_id'], unique=False)

    # Costos de producción por bolsa de un producto (empaque, etiqueta, etc.)
    op.create_table(
        'product_expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column(
            'category',
            sa.Enum('packaging', 'label', 'supplies', 'other', name='productexpensecategoryenum'),
            nullable=False,
        ),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_product_expense_product_id', 'product_expenses', ['product_id'], unique=False)

    # Costo por bolsa congelado al momento del proceso (NULL = sin calcular)
    op.add_column(
        'detail_roasted_coffees',
        sa.Column('unit_cost', sa.Numeric(precision=12, scale=2), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('detail_roasted_coffees', 'unit_cost')
    op.drop_index('idx_product_expense_product_id', table_name='product_expenses')
    op.drop_table('product_expenses')
    op.drop_index('idx_process_expense_process_id', table_name='process_expenses')
    op.drop_table('process_expenses')
    sa.Enum(name='processexpensecategoryenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='productexpensecategoryenum').drop(op.get_bind(), checkfirst=True)
