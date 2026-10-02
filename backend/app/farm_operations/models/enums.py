"""
Enumeraciones del módulo de cultivo.

Cada enum fija su nombre de tipo en Postgres (`name=` en las columnas) con
prefijo `farm`, para no chocar con tipos de otros módulos y para que modelo
y migración coincidan (plan-migraciones §3).
"""

import enum


class PlotStatusEnum(enum.Enum):
    """Estado del lote: el cierre es definitivo, salvo corrección de un error."""

    active = "active"
    closed = "closed"


class PlotEventTypeEnum(enum.Enum):
    """Tipos de evento en el historial de un lote."""

    zoca = "zoca"
    partial_replant = "partial_replant"
    shade_change = "shade_change"
    closure = "closure"
    reopening = "reopening"
    other = "other"


class SupplyTypeEnum(enum.Enum):
    """Tipos de insumo agrícola del catálogo."""

    fertilizer = "fertilizer"
    phytosanitary = "phytosanitary"
    herbicide = "herbicide"
    amendment = "amendment"
    other = "other"
