"""fix_salestatusenum_values

Revision ID: c147cfdcf7f8
Revises: 31d15787710c
Create Date: 2026-07-01 21:36:43.277155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c147cfdcf7f8'
down_revision: Union[str, Sequence[str], None] = '31d15787710c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the status column, recreate the enum with correct values, re-add the column
    op.execute("ALTER TABLE sales DROP COLUMN IF EXISTS status")
    op.execute("DROP TYPE IF EXISTS salestatusenum")
    op.execute("CREATE TYPE salestatusenum AS ENUM ('completed', 'in_progress')")
    op.execute("ALTER TABLE sales ADD COLUMN status salestatusenum NOT NULL DEFAULT 'in_progress'")
    op.create_index('idx_sale_status', 'sales', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_sale_status', table_name='sales')
    op.execute("ALTER TABLE sales DROP COLUMN IF EXISTS status")
    op.execute("DROP TYPE IF EXISTS salestatusenum")
    op.execute("CREATE TYPE salestatusenum AS ENUM ('completed', 'pending', 'canceled')")
    op.execute("ALTER TABLE sales ADD COLUMN status salestatusenum NOT NULL DEFAULT 'pending'")
