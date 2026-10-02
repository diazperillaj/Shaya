from decimal import Decimal
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field, model_validator

Days = Optional[int]
Percent = Optional[Decimal]


class AlertConfigValues(BaseModel):
    """
    Parámetros de una finca o de un lote. Un valor en null hereda del nivel
    superior (lote → finca → valor por defecto del sistema).
    """

    fertilization_reminder_days: Days = Field(None, ge=1, le=3650)
    irrigation_reminder_days: Days = Field(None, ge=1, le=3650)
    phytosanitary_reminder_days: Days = Field(None, ge=1, le=3650)
    weeding_reminder_days: Days = Field(None, ge=1, le=3650)
    harvest_reminder_days: Days = Field(None, ge=1, le=3650)
    inactivity_alert_days: Days = Field(None, ge=1, le=3650)
    max_drying_days: Days = Field(None, ge=1, le=365)
    min_final_humidity: Percent = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    max_final_humidity: Percent = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    min_fermentation_hours: Days = Field(None, ge=1, le=720)
    max_fermentation_hours: Days = Field(None, ge=1, le=720)
    broca_alert_pct: Percent = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)

    @model_validator(mode="after")
    def ranges_in_order(self):
        for low, high, what in (
            ("min_final_humidity", "max_final_humidity", "humedad final"),
            ("min_fermentation_hours", "max_fermentation_hours", "horas de fermentación"),
        ):
            low_value, high_value = getattr(self, low), getattr(self, high)
            if low_value is not None and high_value is not None and low_value > high_value:
                raise ValueError(f"El mínimo de {what} no puede ser mayor que el máximo")
        return self


class ResolvedValue(BaseModel):
    value: Optional[Decimal] = Field(None, description="Valor efectivo; null = recordatorio desactivado")
    source: Literal["plot", "farm", "default"]
    inherited_value: Optional[Decimal] = Field(
        None, description="Valor que aplicaría sin el valor propio de este nivel"
    )
    inherited_source: Literal["farm", "default"]


class ResolvedAlertConfig(BaseModel):
    """Configuración efectiva, con el nivel del que sale cada valor."""

    farm_id: int
    plot_id: Optional[int]
    values: Dict[str, ResolvedValue]
