from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future, require_other_detail
from app.farm_operations.models.enums import DryingDestinationEnum, DryingMethodEnum, DryingStatusEnum
from app.farm_operations.services.dates import business_today

KG = {"max_digits": 10, "decimal_places": 3}
PERCENT = {"ge": 0, "le": 100, "max_digits": 5, "decimal_places": 2}


class DryingInputItem(BaseModel):
    wet_processing_id: int = Field(..., gt=0)
    wet_kg: Decimal = Field(..., gt=0, description="Café lavado que aporta el beneficio", **KG)


def unique_wet_processings(items: List[DryingInputItem]) -> List[DryingInputItem]:
    ids = [item.wet_processing_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Cada beneficio va una sola vez")
    return items


class DryingFields(BaseModel):
    method: DryingMethodEnum
    other_detail: Optional[str] = Field(None, max_length=150, description="Cuál método, cuando es `other`")
    start_date: date = Field(default_factory=business_today)
    observations: Optional[str] = None

    @field_validator("start_date")
    @classmethod
    def start_not_in_future(cls, value):
        return not_in_future(value, "La fecha de inicio")

    @model_validator(mode="after")
    def other_needs_detail(self):
        require_other_detail(self.method == DryingMethodEnum.other, self.other_detail, "Indica cuál método de secado")
        return self


class DryingCreate(DryingFields):
    farm_id: int = Field(..., gt=0)
    inputs: List[DryingInputItem] = Field(..., min_length=1)

    @field_validator("inputs")
    @classmethod
    def one_per_wet_processing(cls, value):
        return unique_wet_processings(value)


class DryingUpdate(DryingFields):
    pass


class DryingInputsReplace(BaseModel):
    inputs: List[DryingInputItem] = Field(..., min_length=1)

    @field_validator("inputs")
    @classmethod
    def one_per_wet_processing(cls, value):
        return unique_wet_processings(value)


class HumidityCheckCreate(BaseModel):
    check_date: date = Field(default_factory=business_today)
    humidity_pct: Decimal = Field(..., **PERCENT)

    @field_validator("check_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de la medición")


class InventoryData(BaseModel):
    """Datos para registrar el pergamino en el inventario (decisión C1)."""

    full_price: Decimal = Field(
        ..., gt=0, max_digits=12, decimal_places=2,
        description="Precio por carga de 125 kg que asigna el productor",
    )
    purchase_date: date = Field(default_factory=business_today)

    @field_validator("purchase_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de ingreso al inventario")


class DryingCompleteRequest(BaseModel):
    end_date: date = Field(default_factory=business_today)
    final_humidity_pct: Decimal = Field(..., **PERCENT)
    output_kg: Decimal = Field(..., gt=0, description="Pergamino seco que sale", **KG)
    packaging: Optional[str] = Field(None, max_length=150)
    sack_count: Optional[int] = Field(None, ge=1)
    packed_at: Optional[date] = None
    storage_place: Optional[str] = Field(None, max_length=150)
    destination: DryingDestinationEnum
    inventory_data: Optional[InventoryData] = Field(None, description="Obligatorio con destino `inventory`")

    @field_validator("end_date", "packed_at")
    @classmethod
    def dates_not_in_future(cls, value):
        return not_in_future(value, "La fecha")

    @model_validator(mode="after")
    def inventory_needs_its_data(self):
        if self.destination == DryingDestinationEnum.inventory and self.inventory_data is None:
            raise ValueError("Indica el precio por carga para registrar el pergamino en el inventario")
        return self


class DryingInputResponse(BaseModel):
    wet_processing_id: int
    wet_kg: Decimal
    pulped_at: Optional[datetime]
    washed_kg: Optional[Decimal]


class HumidityCheckResponse(BaseModel):
    id: int
    check_date: date
    humidity_pct: Decimal


class CompositionHarvest(BaseModel):
    harvest_id: int
    pass_number: int
    crop_cycle_id: int
    cycle_number: int
    cherry_kg: Decimal


class CompositionPlot(BaseModel):
    plot_id: int
    plot_name: str
    variety: str
    cherry_kg: Decimal
    share_pct: Decimal
    harvests: List[CompositionHarvest]


class DryingResponse(BaseModel):
    id: int
    farm_id: int
    farm_name: str
    status: DryingStatusEnum
    method: DryingMethodEnum
    other_detail: Optional[str]
    start_date: date
    end_date: Optional[date]
    final_humidity_pct: Optional[Decimal]
    output_kg: Optional[Decimal]
    packaging: Optional[str]
    sack_count: Optional[int]
    packed_at: Optional[date]
    storage_place: Optional[str]
    destination: Optional[DryingDestinationEnum]
    observations: Optional[str]
    created_at: datetime
    wet_kg: Decimal = Field(..., description="Café lavado que entró (suma de los aportes)")
    days: int = Field(..., description="Días de secado: hasta el fin o, en curso, hasta hoy")
    cherry_kg_traced: Decimal = Field(..., description="Café cereza de las cosechas que terminó en este secado")
    yield_pct: Optional[Decimal] = Field(None, description="Pergamino seco / cereza trazada (F2)")
    humidity_range: tuple[Optional[Decimal], Optional[Decimal]] = Field(
        ..., description="Rango esperado de humedad final, según la configuración de alertas de la finca"
    )
    parchment_id: Optional[int]
    inputs: List[DryingInputResponse]
    humidity_checks: List[HumidityCheckResponse]
    composition: List[CompositionPlot]
