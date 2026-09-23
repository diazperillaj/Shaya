"""add direction to roasted_movement_details

Revision ID: 4fbb6037b8df
Revises: 82a68a9718aa
Create Date: 2026-07-02 13:23:25.238665

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fbb6037b8df'
down_revision: Union[str, Sequence[str], None] = '82a68a9718aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    direction_enum = sa.Enum('entry', 'exit', name='movementdirectionenum')
    direction_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'roasted_movement_details',
        sa.Column('direction', direction_enum, server_default='exit', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('roasted_movement_details', 'direction')
    sa.Enum(name='movementdirectionenum').drop(op.get_bind(), checkfirst=True)
