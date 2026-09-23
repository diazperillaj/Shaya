"""Changed inventory movements field (processed_id) to (processes_id) changed relationship of tables - V2 (Changed on process_id field the foreign key from processed.id to processes.id)

Revision ID: 8c357c00e71d
Revises: a24bcd5c43e1
Create Date: 2026-06-15 13:57:18.049504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c357c00e71d'
down_revision: Union[str, Sequence[str], None] = 'a24bcd5c43e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Eliminar la Foreign Key antigua que apuntaba a 'processed.id'
    # Nota: Si estás en PostgreSQL, Alembic suele nombrar las FK como 'tabla_columna_fkey'
    op.drop_constraint(
        'inventory_movements_process_id_fkey', 
        'inventory_movements', 
        type_='foreignkey'
    )

    # 2. Crear la nueva Foreign Key apuntando a 'processes.id'
    op.create_foreign_key(
        'inventory_movements_process_id_fkey',
        'inventory_movements',
        'processes',
        ['process_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # 1. Eliminar la nueva Foreign Key
    op.drop_constraint(
        'inventory_movements_process_id_fkey', 
        'inventory_movements', 
        type_='foreignkey'
    )

    # 2. Restaurar la Foreign Key original apuntando a 'processed.id'
    op.create_foreign_key(
        'inventory_movements_process_id_fkey',
        'inventory_movements',
        'processed',
        ['process_id'],
        ['id'],
        ondelete='CASCADE'
    )