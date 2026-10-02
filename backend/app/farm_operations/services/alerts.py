"""
Alertas y recordatorios del módulo de cultivo.

Por ahora contiene los valores por defecto y la resolución de umbrales; el
cálculo de las alertas se agrega con el dashboard (dashboards-alertas §6).
"""

from decimal import Decimal
from typing import Optional

from app.farm_operations.models import AlertConfig

# Valores iniciales de práctica cafetera colombiana (dashboards-alertas §4).
# Son puntos de partida, no verdades agronómicas: cada finca o lote los
# ajusta. None = recordatorio desactivado (el riego, porque la mayoría del
# café es de secano).
DEFAULTS: dict[str, Optional[Decimal]] = {
    "fertilization_reminder_days": Decimal(120),
    "irrigation_reminder_days": None,
    "phytosanitary_reminder_days": Decimal(30),
    "weeding_reminder_days": Decimal(75),
    "harvest_reminder_days": Decimal(15),
    "inactivity_alert_days": Decimal(45),
    "max_drying_days": Decimal(15),
    "min_final_humidity": Decimal(10),
    "max_final_humidity": Decimal(12),
    "min_fermentation_hours": Decimal(10),
    "max_fermentation_hours": Decimal(24),
    "broca_alert_pct": Decimal(2),
}

PARAMETERS = tuple(DEFAULTS)


def resolve(*levels: tuple[str, Optional[AlertConfig]]) -> dict[str, dict]:
    """
    Valor efectivo de cada parámetro y el nivel del que sale.

    Recibe los niveles de mayor a menor prioridad, p. ej.
    `resolve(("plot", config_lote), ("farm", config_finca))`. Un valor NULL
    hereda del nivel siguiente; si ninguno lo define, aplica el default.

    Returns:
        `{parámetro: {"value": ..., "source": "plot" | "farm" | "default"}}`
    """
    resolved = {}
    for name in PARAMETERS:
        for source, config in levels:
            value = getattr(config, name) if config is not None else None
            if value is not None:
                resolved[name] = {"value": value, "source": source}
                break
        else:
            resolved[name] = {"value": DEFAULTS[name], "source": "default"}
    return resolved
