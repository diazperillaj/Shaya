"""remove_unused_models_and_columns

Revision ID: af6c41c2ca15
Revises: 8c357c00e71d
Create Date: 2026-06-15 16:16:59.479139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af6c41c2ca15'
down_revision: Union[str, Sequence[str], None] = '8c357c00e71d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Eliminar restricciones de llave foránea en inventory_movements y parchments
    # Nota: Los nombres de los constraints suelen seguir este patrón. Si fallan por nombre, puedes usar SQL directo.
    op.execute("ALTER TABLE inventory_movements DROP CONSTRAINT IF EXISTS inventory_movements_sale_id_fkey CASCADE;")
    op.execute("ALTER TABLE inventory_movements DROP CONSTRAINT IF EXISTS inventory_movements_toll_process_id_fkey CASCADE;")
    op.execute("ALTER TABLE parchments DROP CONSTRAINT IF EXISTS parchments_processed_id_fkey CASCADE;")
    op.execute("ALTER TABLE parchments DROP CONSTRAINT IF EXISTS parchments_toll_process_id_fkey CASCADE;")
    
    # 2. Eliminar las columnas obsoletas de las tablas que quedan
    op.drop_column('inventory_movements', 'sale_id')
    op.drop_column('inventory_movements', 'toll_process_id')

    # 3. Eliminar por completo las tablas que ya no usas
    op.drop_table('sale_details')
    op.drop_table('fast_sales')
    op.drop_table('sales')
    op.drop_table('toll_processes')
    op.drop_table('processed')

def downgrade() -> None:
    pass
