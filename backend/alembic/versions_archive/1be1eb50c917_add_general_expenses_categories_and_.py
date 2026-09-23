"""add general expenses, expense categories and payment methods

- Crea payment_methods (seed: Efectivo, Nequi, Nu)
- Crea expense_categories
- Crea general_expenses (pestaña Gastos del Excel)
- Agrega payment_method_id a sales (nullable: la venta consolidada de
  feria puede mezclar métodos) con backfill Nequi
- Agrega payment_method_id a fair_sales (NOT NULL) con backfill Nequi

Revision ID: 1be1eb50c917
Revises: c9d2f5e81b34
Create Date: 2026-07-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1be1eb50c917'
down_revision: Union[str, Sequence[str], None] = 'c9d2f5e81b34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ─── payment_methods ──────────────────────────────────────────────────
    op.create_table(
        'payment_methods',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.execute(
        "INSERT INTO payment_methods (name) VALUES ('Efectivo'), ('Nequi'), ('Nu')"
    )

    # ─── expense_categories ───────────────────────────────────────────────
    op.create_table(
        'expense_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # ─── general_expenses ─────────────────────────────────────────────────
    op.create_table(
        'general_expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('payment_method_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['category_id'], ['expense_categories.id'], ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['payment_method_id'], ['payment_methods.id'], ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_general_expense_date', 'general_expenses', ['expense_date'])
    op.create_index(
        'idx_general_expense_category_id', 'general_expenses', ['category_id']
    )

    # ─── sales.payment_method_id (nullable + backfill Nequi) ──────────────
    op.add_column('sales', sa.Column('payment_method_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sales_payment_method_id',
        'sales', 'payment_methods',
        ['payment_method_id'], ['id'],
        ondelete='RESTRICT',
    )
    op.execute(
        "UPDATE sales SET payment_method_id = "
        "(SELECT id FROM payment_methods WHERE name = 'Nequi')"
    )

    # ─── fair_sales.payment_method_id (backfill Nequi, luego NOT NULL) ────
    op.add_column(
        'fair_sales', sa.Column('payment_method_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_fair_sales_payment_method_id',
        'fair_sales', 'payment_methods',
        ['payment_method_id'], ['id'],
        ondelete='RESTRICT',
    )
    op.execute(
        "UPDATE fair_sales SET payment_method_id = "
        "(SELECT id FROM payment_methods WHERE name = 'Nequi')"
    )
    op.alter_column('fair_sales', 'payment_method_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_fair_sales_payment_method_id', 'fair_sales', type_='foreignkey')
    op.drop_column('fair_sales', 'payment_method_id')

    op.drop_constraint('fk_sales_payment_method_id', 'sales', type_='foreignkey')
    op.drop_column('sales', 'payment_method_id')

    op.drop_index('idx_general_expense_category_id', table_name='general_expenses')
    op.drop_index('idx_general_expense_date', table_name='general_expenses')
    op.drop_table('general_expenses')
    op.drop_table('expense_categories')
    op.drop_table('payment_methods')
