"""Fragmentos de schema compartidos por las definiciones de tools."""

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


def params(properties: dict, required: list[str] | None = None) -> dict:
    """Envuelve las propiedades en un schema de objeto cerrado."""
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }
