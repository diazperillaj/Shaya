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


class CycleStatusEnum(enum.Enum):
    """Estado del ciclo productivo de un lote: solo uno activo por lote."""

    active = "active"
    closed = "closed"


class FertilizationMethodEnum(enum.Enum):
    """Forma de aplicar el fertilizante."""

    soil = "soil"
    foliar = "foliar"


class SeverityEnum(enum.Enum):
    """Severidad observada en un monitoreo de plagas."""

    low = "low"
    medium = "medium"
    high = "high"


class IntensityEnum(enum.Enum):
    """Intensidad de una floración."""

    low = "low"
    medium = "medium"
    high = "high"


class CulturalPracticeTypeEnum(enum.Enum):
    """Labores culturales del cafetal."""

    weeding = "weeding"
    pruning = "pruning"
    shade_regulation = "shade_regulation"
    amendment = "amendment"
    other = "other"
