"""move process expenses to general expenses

Los gastos de un proceso de maquila dejan de vivir en su propia tabla y
pasan a ser gastos generales asociados al proceso:

- `general_expenses` gana `process_id` (NULL = gasto sin proceso; FK
  RESTRICT: un proceso con gastos no puede eliminarse).
- Se aseguran en el catálogo las categorías que reemplazan al enum de
  `process_expenses`: transport → Transporte, labor → Mano de obra,
  supplies → Insumos, other → Otro.
- Las filas de `process_expenses` se copian a `general_expenses` con su
  proceso, fecha, valor y autor; las observaciones pasan a ser el motivo
  (o el nombre de la categoría si estaban vacías) y el método de pago
  queda sin especificar.
- Se eliminan `process_expenses` y su tipo enum.

El downgrade devuelve los gastos con proceso a `process_expenses`
(categorías sin equivalente quedan como `other`; el método de pago se
pierde) y deja las categorías del catálogo como están.

Revision ID: 1e889c6528ea
Revises: dd940c212d49
Create Date: 2026-10-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e889c6528ea'
down_revision: Union[str, Sequence[str], None] = 'dd940c212d49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Equivalencia entre el enum de process_expenses y el catálogo de categorías
CATEGORY_MAP = (
    ('transport', 'Transporte'),
    ('labor', 'Mano de obra'),
    ('supplies', 'Insumos'),
    ('other', 'Otro'),
)

CATEGORY_VALUES = ", ".join(f"('{code}', '{name}')" for code, name in CATEGORY_MAP)


def upgrade() -> None:
    op.add_column('general_expenses', sa.Column('process_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'general_expenses_process_id_fkey', 'general_expenses', 'processes',
        ['process_id'], ['id'], ondelete='RESTRICT',
    )
    op.create_index('idx_general_expense_process_id', 'general_expenses', ['process_id'])

    op.execute(
        f"""
        INSERT INTO expense_categories (name)
        SELECT m.name
        FROM (VALUES {CATEGORY_VALUES}) AS m(code, name)
        WHERE NOT EXISTS (
            SELECT 1 FROM expense_categories c WHERE lower(c.name) = lower(m.name)
        )
        """
    )

    op.execute(
        f"""
        INSERT INTO general_expenses
            (expense_date, amount, category_id, payment_method_id,
             process_id, description, created_by)
        SELECT pe.expense_date, pe.amount, c.id, NULL,
               pe.process_id,
               COALESCE(NULLIF(trim(pe.observations), ''), m.name),
               pe.created_by
        FROM process_expenses pe
        JOIN (VALUES {CATEGORY_VALUES}) AS m(code, name)
            ON m.code = pe.category::text
        JOIN expense_categories c ON lower(c.name) = lower(m.name)
        ORDER BY pe.id
        """
    )

    op.drop_table('process_expenses')
    op.execute('DROP TYPE processexpensecategoryenum')


def downgrade() -> None:
    op.create_table(
        'process_expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column(
            'category',
            sa.Enum('transport', 'labor', 'supplies', 'other', name='processexpensecategoryenum'),
            nullable=False,
        ),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='process_expenses_pkey'),
        sa.ForeignKeyConstraint(
            ['process_id'], ['processes.id'],
            name='process_expenses_process_id_fkey', ondelete='RESTRICT',
        ),
        sa.ForeignKeyConstraint(
            ['created_by'], ['users.id'],
            name='process_expenses_created_by_fkey', ondelete='SET NULL',
        ),
    )
    op.create_index('idx_process_expense_process_id', 'process_expenses', ['process_id'])

    op.execute(
        f"""
        INSERT INTO process_expenses
            (process_id, category, amount, expense_date, observations, created_by)
        SELECT g.process_id,
               COALESCE(m.code, 'other')::processexpensecategoryenum,
               g.amount, g.expense_date, g.description, g.created_by
        FROM general_expenses g
        JOIN expense_categories c ON c.id = g.category_id
        LEFT JOIN (VALUES {CATEGORY_VALUES}) AS m(code, name)
            ON lower(m.name) = lower(c.name)
        WHERE g.process_id IS NOT NULL
        ORDER BY g.id
        """
    )
    op.execute('DELETE FROM general_expenses WHERE process_id IS NOT NULL')

    op.drop_index('idx_general_expense_process_id', table_name='general_expenses')
    op.drop_constraint('general_expenses_process_id_fkey', 'general_expenses', type_='foreignkey')
    op.drop_column('general_expenses', 'process_id')
