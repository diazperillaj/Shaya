"""
Puerto LLMClient: el agente solo conoce esta interfaz. Cambiar de proveedor
(Groq → OpenAI → otro) es escribir otro adaptador; el loop no se toca.
"""

from dataclasses import dataclass, field
from typing import AsyncIterator, Protocol


@dataclass(frozen=True)
class LLMToolCall:
    id: str
    name: str
    arguments: dict          # parseados (dict vacío si el JSON vino malformado)
    raw_arguments: str       # tal cual los emitió el modelo (para re-enviarlos)


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ToolCallsEvent:
    calls: list[LLMToolCall]


@dataclass(frozen=True)
class UsageEvent:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class DoneEvent:
    finish_reason: str | None = None


LLMEvent = TextDelta | ToolCallsEvent | UsageEvent | DoneEvent


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "UsageEvent") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens

    def as_dict(self) -> dict:
        return {"input": self.input_tokens, "output": self.output_tokens}


class LLMClient(Protocol):
    def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> AsyncIterator[LLMEvent]:
        """Stream de una completion con tool calling."""
        ...

    async def complete_light(self, system: str, user: str, max_tokens: int = 60) -> str:
        """Completion corta y barata (títulos, resúmenes) con el modelo light."""
        ...
