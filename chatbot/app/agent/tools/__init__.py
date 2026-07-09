"""
Registro central de tools. Agregar un dominio nuevo = crear su módulo con
TOOLS y sumarlo a _MODULES (receta de escalabilidad §10 del doc maestro).
"""

from app.agent.registry import ToolRegistry
from app.agent.tools import (
    common,
    customers,
    expenses,
    inventory,
    processes,
    purchases,
    sales,
)

_MODULES = [common, sales, customers, inventory, processes, expenses, purchases]


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for module in _MODULES:
        for spec in module.TOOLS:
            registry.register(spec)
    return registry
