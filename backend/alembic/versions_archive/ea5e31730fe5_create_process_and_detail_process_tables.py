"""create process and detail_process tables

Revision ID: ea5e31730fe5
Revises: 674f8dbc90fa
Create Date: 2026-04-28 21:25:37.436715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea5e31730fe5'
down_revision: Union[str, Sequence[str], None] = '674f8dbc90fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "processes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("process_date", sa.Date(), nullable=False),
        sa.Column("parchment_id", sa.Integer(), nullable=False),
        sa.Column("parchment_kg", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("resultant_kg", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("yield_percentage", sa.Numeric(precision=7, scale=3), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("iva", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parchment_id"],
            ["parchments.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_process_invoice_number", "processes", ["invoice_number"], unique=False)
    op.create_index("idx_process_process_date", "processes", ["process_date"], unique=False)
    op.create_index("idx_process_parchment_id", "processes", ["parchment_id"], unique=False)

    op.create_table(
        "detail_processes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("process_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("bag_quantity", sa.Integer(), nullable=False),
        sa.Column("grams_per_bag", sa.Integer(), nullable=False),
        sa.Column("unit_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("iva", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["process_id"],
            ["processes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("detail_processes")
    op.drop_index("idx_process_parchment_id", table_name="processes")
    op.drop_index("idx_process_process_date", table_name="processes")
    op.drop_index("idx_process_invoice_number", table_name="processes")
    op.drop_table("processes")
