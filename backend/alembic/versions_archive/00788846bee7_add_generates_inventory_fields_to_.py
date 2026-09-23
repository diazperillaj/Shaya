from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "4f2c8c91a1b3"
down_revision: Union[str, None] = "ea5e31730fe5"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column(
        "products",
        sa.Column(
            "generates_inventory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "presentation_grams",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Quitar default persistente en DB
    op.alter_column(
        "products",
        "generates_inventory",
        server_default=None,
    )


def downgrade() -> None:

    op.drop_column("products", "presentation_grams")
    op.drop_column("products", "generates_inventory")