"""Tablas iniciales del chatbot (schema chat)

Revision ID: 0001_chat_schema
Revises:
Create Date: 2026-07-08

El schema chat lo crea scripts/init_db_roles.sql (requiere privilegios que
chatbot_app no tiene). Esta migración solo crea tablas: 100% aditiva.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_chat_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("entities", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="chat",
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("chat.conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=True),
        sa.Column("tool_input", JSONB(), nullable=True),
        sa.Column("tool_result", JSONB(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="chat",
    )
    op.create_index("ix_chat_messages_conv", "messages", ["conversation_id", "id"], schema="chat")


def downgrade() -> None:
    op.drop_index("ix_chat_messages_conv", table_name="messages", schema="chat")
    op.drop_table("messages", schema="chat")
    op.drop_table("conversations", schema="chat")
