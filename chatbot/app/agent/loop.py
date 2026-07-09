"""
Loop del agente: tool calling iterativo con barandillas programáticas.

El LLM decide qué consultar; este loop impone los límites (iteraciones,
timeout por tool, tope de tamaño de resultados) y emite eventos que el
ChatService convierte en SSE y persiste.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator

import anyio

from app.agent.registry import ToolRegistry, serialize_result
from app.core.config import settings
from app.services.llm.base import (
    DoneEvent,
    LLMClient,
    LLMUsage,
    TextDelta,
    ToolCallsEvent,
    UsageEvent,
)

logger = logging.getLogger("chatbot.agent")


# ── Eventos que emite el loop ────────────────────────────────────────
@dataclass(frozen=True)
class StatusEvent:
    tool: str
    label: str


@dataclass(frozen=True)
class TextDeltaEvent:
    text: str


@dataclass(frozen=True)
class ToolExecutedEvent:
    """Para persistencia/auditoría de cada tool call."""

    name: str
    arguments: dict
    result: dict
    is_error: bool
    latency_ms: int


@dataclass(frozen=True)
class FinalEvent:
    text: str
    usage: LLMUsage
    iterations: int
    tools_used: list[str] = field(default_factory=list)


AgentEvent = StatusEvent | TextDeltaEvent | ToolExecutedEvent | FinalEvent


class AgentLoop:
    def __init__(self, llm: LLMClient, registry: ToolRegistry) -> None:
        self._llm = llm
        self._registry = registry
        self._tool_defs = registry.definitions()

    async def run(self, messages: list[dict]) -> AsyncIterator[AgentEvent]:
        """
        `messages` llega con system + historial + turno del usuario y se
        MUTA agregando los turnos assistant/tool de cada iteración.
        """
        usage = LLMUsage()
        tools_used: list[str] = []
        text_parts: list[str] = []

        for iteration in range(1, settings.CHAT_MAX_ITERATIONS + 1):
            text_parts = []
            tool_calls = None

            async for event in self._llm.stream_chat(messages, tools=self._tool_defs):
                if isinstance(event, TextDelta):
                    text_parts.append(event.text)
                    yield TextDeltaEvent(text=event.text)
                elif isinstance(event, ToolCallsEvent):
                    tool_calls = event.calls
                elif isinstance(event, UsageEvent):
                    usage.add(event)
                elif isinstance(event, DoneEvent):
                    pass

            if not tool_calls:
                yield FinalEvent(
                    text="".join(text_parts),
                    usage=usage,
                    iterations=iteration,
                    tools_used=tools_used,
                )
                return

            # Turno assistant con los tool calls, tal cual los emitió el modelo
            messages.append(
                {
                    "role": "assistant",
                    "content": "".join(text_parts) or None,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {"name": call.name, "arguments": call.raw_arguments},
                        }
                        for call in tool_calls
                    ],
                }
            )

            # Todos los resultados vuelven en mensajes `tool` de esta misma vuelta
            for call in tool_calls:
                yield StatusEvent(tool=call.name, label=self._registry.label(call.name))
                started = time.monotonic()
                result, is_error = await self._execute(call.name, call.arguments)
                latency_ms = int((time.monotonic() - started) * 1000)

                tools_used.append(call.name)
                yield ToolExecutedEvent(
                    name=call.name,
                    arguments=call.arguments,
                    result=result,
                    is_error=is_error,
                    latency_ms=latency_ms,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": serialize_result(result),
                    }
                )

        # Tope de iteraciones: última llamada SIN tools para cerrar con lo disponible
        logger.warning("Turno alcanzó el tope de %s iteraciones", settings.CHAT_MAX_ITERATIONS)
        messages.append(
            {
                "role": "user",
                "content": (
                    "[Sistema: límite de consultas alcanzado. Responde ahora con la "
                    "información ya obtenida y acláralo si quedó incompleta.]"
                ),
            }
        )
        text_parts = []
        async for event in self._llm.stream_chat(messages, tools=None):
            if isinstance(event, TextDelta):
                text_parts.append(event.text)
                yield TextDeltaEvent(text=event.text)
            elif isinstance(event, UsageEvent):
                usage.add(event)

        yield FinalEvent(
            text="".join(text_parts),
            usage=usage,
            iterations=settings.CHAT_MAX_ITERATIONS,
            tools_used=tools_used,
        )

    async def _execute(self, name: str, arguments: dict) -> tuple[dict, bool]:
        """Ejecuta la tool (síncrona, hace SQL+Pandas) en un thread, con timeout."""
        try:
            with anyio.fail_after(settings.CHAT_TOOL_TIMEOUT_S):
                return await anyio.to_thread.run_sync(
                    self._registry.execute, name, arguments
                )
        except TimeoutError:
            logger.error(
                "Tool %s superó el timeout de %ss con argumentos %s",
                name, settings.CHAT_TOOL_TIMEOUT_S, arguments,
            )
            return (
                {"error": f"La consulta {name} tardó demasiado y fue cancelada. "
                          "Intenta con un rango o filtro más pequeño."},
                True,
            )
