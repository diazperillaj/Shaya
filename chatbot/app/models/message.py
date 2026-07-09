from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func as sql_func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Message(Base):
    """
    Un mensaje del historial: turno del usuario, respuesta del asistente
    o ejecución de una tool (auditoría completa: input, resultado, tokens).
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_chat_messages_conv", "conversation_id", "id"),
        {"schema": "chat"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat.conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant | tool
    content: Mapped[list | dict] = mapped_column(JSONB, nullable=False)  # bloques [{type:"text",...}]
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    conversation = relationship("Conversation", back_populates="messages")
