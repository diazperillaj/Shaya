from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis import get_redis
from app.core.security import CurrentUser, get_current_user
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationListItem,
    ConversationOut,
)
from app.schemas.message import MessageIn
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/conversations", tags=["chat"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # nginx: no bufferizar el stream
}


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return ConversationService(db).create(user.id, payload.title)


@router.get("", response_model=list[ConversationListItem])
def list_conversations(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    items = ConversationService(db).list_for_user(user.id)
    return [
        ConversationListItem(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            preview=preview,
        )
        for conv, preview in items
    ]


@router.get("/{conv_id}", response_model=ConversationDetail)
def get_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return ConversationService(db).get_with_messages(conv_id, user)


@router.delete("/{conv_id}", status_code=204)
async def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    service = ConversationService(db)
    conv = service.get_owned(conv_id, user)
    service.delete(conv)
    await MemoryService(get_redis()).forget(conv_id)


@router.post("/{conv_id}/messages")
async def send_message(
    conv_id: int,
    payload: MessageIn,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Turno del asistente: la respuesta es un stream SSE
    (status | text_delta | done | error)."""
    service = ChatService(db)
    conv = service.conversations.get_owned(conv_id, user)
    return StreamingResponse(
        service.stream_turn(conv, user, payload.text),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
