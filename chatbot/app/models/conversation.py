from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func as sql_func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Conversation(Base):
    """
    Conversación del asistente. Vive en el schema chat (fuente de verdad);
    Redis solo guarda la copia caliente reconstruible.

    user_id referencia al usuario del backend pero SIN FK cross-schema:
    la pertenencia se valida por el JWT en cada request.
    """

    __tablename__ = "conversations"
    __table_args__ = {"schema": "chat"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)      # fase 2
    entities: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")  # fase 2
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now(), onupdate=sql_func.now()
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )
