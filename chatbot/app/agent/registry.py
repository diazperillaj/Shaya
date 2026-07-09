"""
ToolRegistry: catálogo declarativo de herramientas del agente.

Cada tool = JSON Schema (formato OpenAI function) + executor de la capa
analytics + etiqueta para el evento SSE `status`. Registrar un dominio nuevo
es agregar su ToolSpec en agent/tools/ — el loop no cambia (receta §10 del doc).
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable

from jsonschema import Draft202012Validator

from app.analytics.base import ToolError

logger = logging.getLogger("chatbot.tools")

# ~2.000 tokens ≈ 8.000 caracteres: tope duro de cada resultado de tool
MAX_RESULT_CHARS = 8_000


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]          # JSON Schema de los argumentos
    executor: Callable[..., dict]       # función de app/analytics (pura, síncrona)
    label: str                          # texto del evento SSE `status`


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._validators: dict[str, Draft202012Validator] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool duplicada: {spec.name}")
        self._tools[spec.name] = spec
        self._validators[spec.name] = Draft202012Validator(spec.parameters)

    def definitions(self) -> list[dict]:
        """Definiciones en formato OpenAI tools (orden determinista → caché estable)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                },
            }
            for _, spec in sorted(self._tools.items())
        ]

    def label(self, name: str) -> str:
        spec = self._tools.get(name)
        return spec.label if spec else f"Ejecutando {name}…"

    def execute(self, name: str, args: dict[str, Any]) -> tuple[dict, bool]:
        """
        Ejecuta una tool y devuelve (resultado, is_error).

        Nunca lanza: todo error se convierte en un mensaje accionable para el
        LLM y se reporta a consola con tool + argumentos + traceback (norma de
        calidad: nunca un 500 silencioso por una tool fallida).
        """
        spec = self._tools.get(name)
        if spec is None:
            return {"error": f"La herramienta '{name}' no existe."}, True

        errores = [
            f"{'/'.join(str(p) for p in e.path) or 'raíz'}: {e.message}"
            for e in self._validators[name].iter_errors(args)
        ]
        if errores:
            logger.warning("Tool %s: argumentos inválidos %s → %s", name, args, errores)
            return (
                {
                    "error": f"Argumentos inválidos para {name}: " + "; ".join(errores[:3]),
                    "esquema_esperado": list(spec.parameters.get("properties", {}).keys()),
                },
                True,
            )

        try:
            return spec.executor(**args), False
        except ToolError as exc:
            # Error de negocio esperado (id inexistente, rango inválido…)
            logger.info("Tool %s(%s) → ToolError: %s", name, args, exc)
            return {"error": str(exc)}, True
        except Exception:
            # Error interno: reporte completo en consola (dónde y por qué)
            logger.exception("Tool %s falló con argumentos %s", name, args)
            return (
                {
                    "error": (
                        f"Error interno ejecutando {name}. Informa al usuario que esa "
                        "consulta falló y sugiérele reformularla."
                    )
                },
                True,
            )


def serialize_result(result: dict) -> str:
    """
    Serializa el resultado para el mensaje `tool` del LLM, con tope duro de
    tamaño: si excede, se recortan filas (nunca el resumen) y se marca truncado.
    """
    payload = json.dumps(result, ensure_ascii=False, default=str)
    if len(payload) <= MAX_RESULT_CHARS:
        return payload

    recortado = dict(result)
    filas = list(recortado.get("filas") or [])
    while filas and len(payload) > MAX_RESULT_CHARS:
        filas = filas[: max(len(filas) // 2, 1)]
        if len(filas) == 1 and len(payload) > MAX_RESULT_CHARS:
            filas = []
        recortado["filas"] = filas
        recortado["truncado"] = True
        advertencias = list(recortado.get("advertencias") or [])
        if not any("recort" in a for a in advertencias):
            advertencias.append("Resultado recortado por tamaño: pide un filtro más específico.")
        recortado["advertencias"] = advertencias
        payload = json.dumps(recortado, ensure_ascii=False, default=str)
    return payload
