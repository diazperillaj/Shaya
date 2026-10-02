from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.models.enums import PlotEventTypeEnum, PlotStatusEnum
from app.farm_operations.services.dates import business_today

# Tipos de evento que se registran a mano: el cierre y la reapertura tienen
# sus propias acciones (close / reopen).
MANUAL_EVENT_TYPES = {
    PlotEventTypeEnum.zoca,
    PlotEventTypeEnum.partial_replant,
    PlotEventTypeEnum.shade_change,
    PlotEventTypeEnum.other,
}


def not_in_future(value: Optional[date], what: str) -> Optional[date]:
    if value is not None and value > business_today():
        raise ValueError(f"{what} no puede ser futura")
    return value


class PlotBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    # Terreno
    area: Optional[Decimal] = Field(None, gt=0, max_digits=8, decimal_places=2, description="Hectáreas")
    slope: Optional[Decimal] = Field(None, ge=0, max_digits=5, decimal_places=2, description="% de pendiente")
    soil_type: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)

    # Siembra
    variety: str = Field(..., min_length=1, max_length=100)
    planting_date: Optional[date] = None
    initial_age_years: Optional[Decimal] = Field(
        None, ge=0, max_digits=4, decimal_places=1,
        description="Edad del cultivo al registrarlo, si ya estaba establecido",
    )
    seedling_count: Optional[int] = Field(None, gt=0)
    row_spacing_m: Optional[Decimal] = Field(None, gt=0, max_digits=4, decimal_places=2)
    plant_spacing_m: Optional[Decimal] = Field(None, gt=0, max_digits=4, decimal_places=2)
    shade_type: Optional[str] = Field(None, max_length=100)

    # Procedencia de la semilla
    seed_supplier: Optional[str] = Field(None, max_length=255)
    seed_origin_place: Optional[str] = Field(None, max_length=255)
    seed_purchase_date: Optional[date] = None
    seed_cost: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)

    observations: Optional[str] = None

    @field_validator("planting_date")
    @classmethod
    def planting_not_in_future(cls, value):
        return not_in_future(value, "La fecha de siembra")

    @field_validator("seed_purchase_date")
    @classmethod
    def purchase_not_in_future(cls, value):
        return not_in_future(value, "La fecha de compra de la semilla")

    @model_validator(mode="after")
    def planting_date_or_age(self):
        if self.planting_date is None and self.initial_age_years is None:
            raise ValueError("Indica la fecha de siembra o la edad actual del cultivo")
        return self


class PlotCreate(PlotBase):
    farm_id: int = Field(..., gt=0)
    renewed_from_plot_id: Optional[int] = Field(
        None, gt=0, description="Lote cerrado que se vuelve a sembrar en el mismo terreno"
    )


class PlotUpdate(PlotBase):
    pass


class PlotResponse(BaseModel):
    id: int
    farm_id: int
    farm_name: str
    name: str
    status: PlotStatusEnum
    renewed_from_plot_id: Optional[int]
    renewed_by_plot_id: Optional[int]
    area: Optional[Decimal]
    slope: Optional[Decimal]
    soil_type: Optional[str]
    location: Optional[str]
    variety: str
    planting_date: Optional[date]
    initial_age_years: Optional[Decimal]
    seedling_count: Optional[int]
    row_spacing_m: Optional[Decimal]
    plant_spacing_m: Optional[Decimal]
    shade_type: Optional[str]
    seed_supplier: Optional[str]
    seed_origin_place: Optional[str]
    seed_purchase_date: Optional[date]
    seed_cost: Optional[Decimal]
    closed_at: Optional[date]
    observations: Optional[str]
    created_at: datetime
    effective_age_years: Decimal = Field(
        ..., description="Años desde la siembra o la última zoca (congelada al cierre)"
    )
    last_zoca_date: Optional[date]


class RenewalDefaults(BaseModel):
    """Datos del terreno para precargar el lote que lo vuelve a sembrar."""

    farm_id: int
    renewed_from_plot_id: int
    name: str
    area: Optional[Decimal]
    slope: Optional[Decimal]
    soil_type: Optional[str]
    location: Optional[str]


class PlotCloseRequest(BaseModel):
    closed_at: date = Field(default_factory=business_today)
    description: Optional[str] = None

    @field_validator("closed_at")
    @classmethod
    def closed_not_in_future(cls, value):
        return not_in_future(value, "La fecha de cierre")


class PlotReopenRequest(BaseModel):
    description: Optional[str] = Field(None, description="Por qué se corrige el cierre")


class PlotEventCreate(BaseModel):
    event_type: PlotEventTypeEnum
    event_date: date
    other_detail: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None

    @field_validator("event_type")
    @classmethod
    def manual_type(cls, value):
        if value not in MANUAL_EVENT_TYPES:
            raise ValueError("El cierre y la reapertura se registran con sus propias acciones")
        return value

    @field_validator("event_date")
    @classmethod
    def event_not_in_future(cls, value):
        return not_in_future(value, "La fecha del evento")

    @model_validator(mode="after")
    def other_needs_detail(self):
        if self.event_type == PlotEventTypeEnum.other and not (self.other_detail or "").strip():
            raise ValueError("Indica cuál evento es")
        return self


class PlotEventResponse(BaseModel):
    id: int
    plot_id: int
    event_type: PlotEventTypeEnum
    other_detail: Optional[str]
    event_date: date
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
