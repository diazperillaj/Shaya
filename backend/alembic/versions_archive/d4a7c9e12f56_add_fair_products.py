"""add fair products catalog and product sales in fairs

- Crea fair_products (catálogo global: café preparado, galletas, ...)
  con precio por defecto.
- fair_sales.fair_inventory_id pasa a nullable y se agrega
  fair_product_id (RESTRICT): una venta de feria referencia inventario
  (café) o un producto de feria, exactamente uno (CHECK).

Revision ID: d4a7c9e12f56
Revises: 1be1eb50c917
Create Date: 2026-07-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a7c9e12f56'
down_revision: Union[str, Sequence[str], None] = '1be1eb50c917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ─── fair_products ────────────────────────────────────────────────────
    op.create_table(
        'fair_products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('default_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # ─── fair_sales: inventario o producto de feria ───────────────────────
    op.alter_column(
        'fair_sales', 'fair_inventory_id',
        existing_type=sa.Integer(), nullable=True,
    )
    op.add_column('fair_sales', sa.Column('fair_product_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_fair_sales_fair_product_id', 'fair_sales', 'fair_products',
        ['fair_product_id'], ['id'], ondelete='RESTRICT',
    )
    op.create_index('idx_fair_sale_product_id', 'fair_sales', ['fair_product_id'], unique=False)
    op.create_check_constraint(
        'ck_fair_sale_item_source', 'fair_sales',
        '(fair_inventory_id IS NULL) != (fair_product_id IS NULL)',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_fair_sale_item_source', 'fair_sales', type_='check')
    op.drop_index('idx_fair_sale_product_id', table_name='fair_sales')
    op.drop_constraint('fk_fair_sales_fair_product_id', 'fair_sales', type_='foreignkey')
    # Las ventas de producto quedarían huérfanas: eliminarlas antes de
    # restaurar el NOT NULL.
    op.execute('DELETE FROM fair_sales WHERE fair_inventory_id IS NULL')
    op.drop_column('fair_sales', 'fair_product_id')
    op.alter_column(
        'fair_sales', 'fair_inventory_id',
        existing_type=sa.Integer(), nullable=False,
    )
    op.drop_table('fair_products')
