"""Fragmentos de schema compartidos por las definiciones de tools."""

from typing import Any

FECHA = {
    "type": "string",
    "description": (
        "YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS (hora Bogotá). "
        "Omitir = sin límite en ese extremo."
    ),
}

ORDEN = {"type": "string", "enum": ["asc", "desc"], "description": "Orden del ranking. Default: desc."}

TOP = {
    "type": "integer",
    "minimum": 1,
    "maximum": 50,
    "description": "Máximo de filas a devolver (default 10, tope 50).",
}


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    """Permite null en un property: los modelos tipo llama emiten null en los
    parámetros opcionales que no usan, y Groq valida los argumentos contra el
    schema — sin esto, la generación completa falla ('Failed to call a function')."""
    out = dict(schema)
    if "enum" in out and None not in out["enum"]:
        out["enum"] = [*out["enum"], None]
    tipo = out.get("type")
    if isinstance(tipo, str):
        out["type"] = [tipo, "null"]
    return out


def params(properties: dict, required: list[str] | None = None) -> dict:
    """Schema de objeto cerrado. Todo property que no sea required se vuelve
    nullable automáticamente (el registry además descarta los null antes de
    ejecutar, para que apliquen los defaults de Python)."""
    required = required or []
    return {
        "type": "object",
        "properties": {
            name: (schema if name in required else _nullable(schema))
            for name, schema in properties.items()
        },
        "required": required,
        "additionalProperties": False,
    }
