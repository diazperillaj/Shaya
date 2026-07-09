"""
Adaptador para cualquier API OpenAI-compatible (Groq en desarrollo).
El proveedor se cambia solo con LLM_BASE_URL / LLM_MODEL / LLM_API_KEY.
"""

import json
import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.llm.base import (
    DoneEvent,
    LLMEvent,
    LLMToolCall,
    TextDelta,
    ToolCallsEvent,
    UsageEvent,
)

logger = logging.getLogger("chatbot.llm")


class OpenAICompatibleClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            timeout=60.0,
        )

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> AsyncIterator[LLMEvent]:
        kwargs: dict = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        stream = await self._client.chat.completions.create(**kwargs)

        # Los tool calls llegan en deltas parciales indexados: se acumulan aquí
        pending: dict[int, dict] = {}
        finish_reason: str | None = None

        async for chunk in stream:
            if chunk.usage:  # último chunk con stream_options.include_usage
                yield UsageEvent(
                    input_tokens=chunk.usage.prompt_tokens or 0,
                    output_tokens=chunk.usage.completion_tokens or 0,
                )
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta and delta.content:
                yield TextDelta(text=delta.content)

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    slot = pending.setdefault(
                        tc.index, {"id": "", "name": "", "arguments": ""}
                    )
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function and tc.function.name:
                        slot["name"] += tc.function.name
                    if tc.function and tc.function.arguments:
                        slot["arguments"] += tc.function.arguments

            if choice.finish_reason:
                finish_reason = choice.finish_reason

        if pending:
            yield ToolCallsEvent(calls=[_to_call(slot) for _, slot in sorted(pending.items())])

        yield DoneEvent(finish_reason=finish_reason)

    async def complete_light(self, system: str, user: str, max_tokens: int = 60) -> str:
        response = await self._client.chat.completions.create(
            model=settings.LLM_MODEL_LIGHT,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return (response.choices[0].message.content or "").strip()


def _to_call(slot: dict) -> LLMToolCall:
    raw = slot["arguments"] or "{}"
    try:
        arguments = json.loads(raw)
        if not isinstance(arguments, dict):
            arguments = {}
    except json.JSONDecodeError:
        logger.warning("Argumentos de tool malformados: %s", raw[:200])
        arguments = {}
    return LLMToolCall(id=slot["id"], name=slot["name"], arguments=arguments, raw_arguments=raw)
