import json
from typing import Any


def sse(event: str, data: dict[str, Any]) -> str:
    """Formatea un evento SSE (contrato con el frontend: status | text_delta | done | error)."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_status(tool: str, label: str) -> str:
    return sse("status", {"tool": tool, "label": label})


def sse_text_delta(text: str) -> str:
    return sse("text_delta", {"text": text})


def sse_done(message_id: int, usage: dict, latency_ms: int) -> str:
    return sse("done", {"message_id": message_id, "usage": usage, "latency_ms": latency_ms})


def sse_error(detail: str) -> str:
    return sse("error", {"detail": detail})
