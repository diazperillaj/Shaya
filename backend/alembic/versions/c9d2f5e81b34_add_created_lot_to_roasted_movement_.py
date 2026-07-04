"""add created_lot to roasted_movement_details

Revision ID: c9d2f5e81b34
Revises: b7c1e4d90a23
Create Date: 2026-07-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d2f5e81b34'
down_revision: Union[str, Sequence[str], None] = 'b7c1e4d90a23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'roasted_movement_details',
        sa.Column('created_lot', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('roasted_movement_details', 'created_lot')
