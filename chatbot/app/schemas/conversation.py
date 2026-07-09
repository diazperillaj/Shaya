from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.message import MessageOut


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationListItem(ConversationOut):
    preview: str | None = None  # último mensaje de texto, recortado


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []
