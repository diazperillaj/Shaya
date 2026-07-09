"""
ChatService: orquesta UN turno completo del asistente.

memoria (Redis) → loop del agente (LLM + tools) → persistencia (Postgres)
→ eventos SSE al frontend. Nunca deja un stream sin evento terminal
(done o error).
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agent.loop import (
    AgentLoop,
    FinalEvent,
    StatusEvent,
    TextDeltaEvent,
    ToolExecutedEvent,
)
from app.agent.prompts import SYSTEM_PROMPT, TITLE_SYSTEM, build_user_turn
from app.agent.tools import build_registry
from app.core.config import settings
from app.core.redis import get_redis
from app.core.security import CurrentUser
from app.models import Conversation
from app.schemas.events import sse_done, sse_error, sse_status, sse_text_delta
from app.services.conversation_service import ConversationService
from app.services.llm.openai_compatible import OpenAICompatibleClient
from app.services.memory_service import MemoryService

logger = logging.getLogger("chatbot.chat")

# Singletons del proceso: el registry y el cliente LLM son inmutables
_registry = build_registry()
_llm = OpenAICompatibleClient()


class ChatService:
    def __init__(self, db: Session) -> None:
        self.conversations = ConversationService(db)
        self.memory = MemoryService(get_redis())
        self.loop = AgentLoop(_llm, _registry)

    async def stream_turn(
        self, conv: Conversation, user: CurrentUser, text: str
    ) -> AsyncIterator[str]:
        """Genera los eventos SSE de un turno. El generador es el dueño del turno."""
        started = time.monotonic()
        try:
            await self.memory.check_rate_limit(user.id)

            history = await self.memory.get_context(self.conversations, conv.id)
            self.conversations.add_user_message(conv, text)

            messages: list[dict] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": build_user_turn(text)},
            ]

            final: FinalEvent | None = None
            tools_note_parts: list[str] = []

            async with asyncio.timeout(settings.CHAT_TURN_TIMEOUT_S):
                async for event in self.loop.run(messages):
                    if isinstance(event, TextDeltaEvent):
                        yield sse_text_delta(event.text)
                    elif isinstance(event, StatusEvent):
                        yield sse_status(event.tool, event.label)
                    elif isinstance(event, ToolExecutedEvent):
                        self.conversations.add_tool_message(
                            conv, event.name, event.arguments, event.result, event.latency_ms
                        )
                        tools_note_parts.append(_tool_note(event))
                    elif isinstance(event, FinalEvent):
                        final = event

            if final is None:  # no debería pasar: el loop siempre emite FinalEvent
                raise RuntimeError("El agente terminó sin respuesta final")

            latency_ms = int((time.monotonic() - started) * 1000)
            msg = self.conversations.add_assistant_message(
                conv,
                final.text,
                input_tokens=final.usage.input_tokens,
                output_tokens=final.usage.output_tokens,
                latency_ms=latency_ms,
                model=settings.LLM_MODEL,
            )
            await self.memory.append_turn(
                conv.id, text, final.text, tools_note="; ".join(tools_note_parts) or None
            )
            if conv.title is None:
                await self._set_title(conv, text)

            logger.info(
                "Turno conv=%s user=%s tools=%s tokens_in=%s tokens_out=%s latencia=%sms",
                conv.id, user.id, final.tools_used,
                final.usage.input_tokens, final.usage.output_tokens, latency_ms,
            )
            yield sse_done(msg.id, final.usage.as_dict(), latency_ms)

        except TimeoutError:
            logger.error("Turno de conv %s superó los %ss", conv.id, settings.CHAT_TURN_TIMEOUT_S)
            yield sse_error("La respuesta tardó demasiado y fue cancelada. Intenta de nuevo.")
        except HTTPException as exc:
            # p. ej. rate limit: el stream ya está abierto, va como evento error
            yield sse_error(str(exc.detail))
        except Exception:
            logger.exception("Turno de conv %s falló", conv.id)
            yield sse_error("Ocurrió un error procesando tu mensaje. Intenta de nuevo.")

    async def _set_title(self, conv: Conversation, first_message: str) -> None:
        """Título con el modelo light; si falla, un recorte del mensaje."""
        try:
            title = await _llm.complete_light(TITLE_SYSTEM, first_message)
        except Exception:
            logger.warning("Fallo generando título para conv %s", conv.id, exc_info=True)
            title = ""
        self.conversations.set_title(conv, title or first_message[:60])


def _tool_note(event: ToolExecutedEvent) -> str:
    """Nota compacta del tool call para la memoria de turnos futuros."""
    resumen = event.result.get("resumen") or event.result.get("error") or {}
    return f"{event.name}→{json.dumps(resumen, ensure_ascii=False, default=str)[:150]}"
