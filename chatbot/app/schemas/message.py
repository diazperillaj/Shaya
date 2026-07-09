from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TextBlock(BaseModel):
    """Bloque de texto. En fase 4 se suman TableBlock y ChartBlock sin
    romper el contrato: el frontend renderiza por type."""

    type: Literal["text"] = "text"
    text: str


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: Any            # lista de bloques (user/assistant) o payload de tool
    tool_name: str | None = None
    created_at: datetime
