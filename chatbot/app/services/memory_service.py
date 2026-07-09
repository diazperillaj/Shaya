"""
Memoria conversacional caliente en Redis (cache-aside).

Redis guarda TODO el historial de la conversación como lista, pero al LLM
solo van los últimos CHAT_HISTORY_WINDOW mensajes (cola FIFO: entra lo nuevo,
sale lo viejo del contexto) — ahorro de tokens sin perder el historial.
Postgres es la fuente de verdad: si Redis está frío, se reconstruye.
"""

import json
import logging

from fastapi import HTTPException
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.services.conversation_service import ConversationService

logger = logging.getLogger("chatbot.memory")

_TOOLS_NOTE_MAX = 400  # chars del apéndice [Datos consultados: …] por turno


def _window_key(conv_id: int) -> str:
    return f"conv:{conv_id}:window"


def _rl_key(user_id: int) -> str:
    return f"ratelimit:{user_id}"


class MemoryService:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get_context(self, conversations: ConversationService, conv_id: int) -> list[dict]:
        """Últimos N mensajes user/assistant en formato OpenAI."""
        key = _window_key(conv_id)
        try:
            items = await self.redis.lrange(key, 0, -1)
        except RedisError:
            logger.warning("Redis no disponible: contexto directo desde Postgres")
            items = None

        if not items:
            history = conversations.history_texts(conv_id)
            if items is not None and history:  # Redis vive pero estaba frío
                try:
                    async with self.redis.pipeline(transaction=False) as pipe:
                        pipe.delete(key)
                        for entry in history:
                            pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
                        pipe.expire(key, settings.CHAT_MEMORY_TTL_S)
                        await pipe.execute()
                except RedisError:
                    logger.warning("No se pudo recalentar Redis para conv %s", conv_id)
            entries = history
        else:
            entries = []
            for raw in items:
                try:
                    entries.append(json.loads(raw))
                except json.JSONDecodeError:
                    logger.warning("Entrada corrupta en %s ignorada", key)

        return entries[-settings.CHAT_HISTORY_WINDOW:]

    async def append_turn(
        self,
        conv_id: int,
        user_text: str,
        assistant_text: str,
        tools_note: str | None = None,
    ) -> None:
        """Agrega el turno completo a la ventana (best-effort: PG ya lo tiene)."""
        content = assistant_text
        if tools_note:
            content += f"\n[Datos consultados: {tools_note[:_TOOLS_NOTE_MAX]}]"
        key = _window_key(conv_id)
        try:
            async with self.redis.pipeline(transaction=False) as pipe:
                pipe.rpush(key, json.dumps({"role": "user", "content": user_text}, ensure_ascii=False))
                pipe.rpush(key, json.dumps({"role": "assistant", "content": content}, ensure_ascii=False))
                pipe.expire(key, settings.CHAT_MEMORY_TTL_S)
                await pipe.execute()
        except RedisError:
            logger.warning("Redis no disponible al guardar el turno de conv %s", conv_id)

    async def forget(self, conv_id: int) -> None:
        try:
            await self.redis.delete(_window_key(conv_id))
        except RedisError:
            pass

    async def check_rate_limit(self, user_id: int) -> None:
        """Tope de mensajes por minuto por usuario (protección de costos LLM)."""
        try:
            key = _rl_key(user_id)
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 60)
        except RedisError:
            return  # sin Redis no bloqueamos el servicio
        if count > settings.CHAT_RATE_LIMIT_PER_MIN:
            raise HTTPException(
                status_code=429,
                detail="Demasiados mensajes por minuto. Espera un momento e intenta de nuevo.",
            )
