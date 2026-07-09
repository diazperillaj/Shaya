"""CRUD del historial (fuente de verdad: PostgreSQL schema chat)."""

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.core.security import CurrentUser
from app.models import Conversation, Message


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Conversaciones ───────────────────────────────────────────────
    def create(self, user_id: int, title: str | None = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_for_user(self, user_id: int) -> list[tuple[Conversation, str | None]]:
        convs = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .all()
        )
        out: list[tuple[Conversation, str | None]] = []
        for conv in convs:
            last = (
                self.db.query(Message)
                .filter(Message.conversation_id == conv.id, Message.role != "tool")
                .order_by(desc(Message.id))
                .first()
            )
            out.append((conv, _preview(last)))
        return out

    def get_owned(self, conv_id: int, user: CurrentUser) -> Conversation:
        conv = self.db.get(Conversation, conv_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        if conv.user_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="No tienes permisos sobre esta conversación")
        return conv

    def get_with_messages(self, conv_id: int, user: CurrentUser) -> Conversation:
        conv = (
            self.db.query(Conversation)
            .options(selectinload(Conversation.messages))
            .filter(Conversation.id == conv_id)
            .first()
        )
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        if conv.user_id != user.id and not user.is_admin:
            raise HTTPException(status_code=403, detail="No tienes permisos sobre esta conversación")
        return conv

    def delete(self, conv: Conversation) -> None:
        self.db.delete(conv)
        self.db.commit()

    def set_title(self, conv: Conversation, title: str) -> None:
        conv.title = title[:200]
        self.db.commit()

    # ── Mensajes ─────────────────────────────────────────────────────
    def add_user_message(self, conv: Conversation, text: str) -> Message:
        return self._add(conv, role="user", content=[{"type": "text", "text": text}])

    def add_tool_message(
        self,
        conv: Conversation,
        name: str,
        tool_input: dict,
        tool_result: dict,
        latency_ms: int,
    ) -> Message:
        return self._add(
            conv,
            role="tool",
            content={"tool": name},
            tool_name=name,
            tool_input=tool_input,
            tool_result=tool_result,
            latency_ms=latency_ms,
        )

    def add_assistant_message(
        self,
        conv: Conversation,
        text: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        model: str,
    ) -> Message:
        return self._add(
            conv,
            role="assistant",
            content=[{"type": "text", "text": text}],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=model,
        )

    def history_texts(self, conv_id: int) -> list[dict]:
        """Historial user/assistant como texto plano (reconstrucción de Redis)."""
        rows = (
            self.db.query(Message)
            .filter(Message.conversation_id == conv_id, Message.role.in_(["user", "assistant"]))
            .order_by(Message.id)
            .all()
        )
        return [
            {"role": row.role, "content": _blocks_to_text(row.content)}
            for row in rows
        ]

    def _add(self, conv: Conversation, **fields) -> Message:
        msg = Message(conversation_id=conv.id, **fields)
        self.db.add(msg)
        conv.updated_at = msg.created_at  # touch para ordenar la lista
        self.db.commit()
        self.db.refresh(msg)
        return msg


def _blocks_to_text(content) -> str:
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return str(content)


def _preview(msg: Message | None) -> str | None:
    if msg is None:
        return None
    text = _blocks_to_text(msg.content)
    return text[:120] + ("…" if len(text) > 120 else "")
