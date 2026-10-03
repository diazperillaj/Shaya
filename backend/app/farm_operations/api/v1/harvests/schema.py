from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future
from app.farm_operations.models.enums import HarvestPaymentTypeEnum, HarvestStatusEnum
from app.farm_operations.services.dates import business_today

MONEY = {"gt": 0, "max_digits": 12, "decimal_places": 2}
KG = {"max_digits": 10, "decimal_places": 3}


# ── Cosechas ──────────────────────────────────────────────────────────────


class HarvestCreate(BaseModel):
    crop_cycle_id: int = Field(..., gt=0)
    start_date: date = Field(default_factory=business_today)
    rate_per_kg: Optional[Decimal] = Field(None, description="Tarifa por kg por defecto de la sesión", **MONEY)
    rate_per_day: Optional[Decimal] = Field(None, description="Valor del jornal por defecto de la sesión", **MONEY)
    observations: Optional[str] = None

    @field_validator("start_date")
    @classmethod
    def start_not_in_future(cls, value):
        return not_in_future(value, "La fecha de inicio")


class HarvestUpdate(BaseModel):
    start_date: date
    rate_per_kg: Optional[Decimal] = Field(None, **MONEY)
    rate_per_day: Optional[Decimal] = Field(None, **MONEY)
    observations: Optional[str] = None
    end_date: Optional[date] = Field(None, description="Solo en cosechas cerradas")
    total_cherry_kg: Optional[Decimal] = Field(None, ge=0, description="Solo en cosechas cerradas", **KG)

    @field_validator("start_date", "end_date")
    @classmethod
    def dates_not_in_future(cls, value):
        return not_in_future(value, "La fecha")

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        return self


class HarvestCloseRequest(BaseModel):
    end_date: date = Field(default_factory=business_today)
    total_cherry_kg: Optional[Decimal] = Field(
        None, ge=0, description="Vacío = suma de los kg registrados en la recolección", **KG
    )

    @field_validator("end_date")
    @classmethod
    def end_not_in_future(cls, value):
        return not_in_future(value, "La fecha de fin")


# ── Recolección diaria ────────────────────────────────────────────────────


class HarvestWorkFields(BaseModel):
    employee_id: int = Field(..., gt=0)
    work_date: date = Field(default_factory=business_today)
    payment_type: HarvestPaymentTypeEnum = HarvestPaymentTypeEnum.per_kg
    kg_collected: Optional[Decimal] = Field(None, gt=0, **KG)
    rate_per_kg: Optional[Decimal] = Field(None, description="Vacío = tarifa de la cosecha", **MONEY)
    day_value: Optional[Decimal] = Field(None, description="Vacío = jornal de la cosecha", **MONEY)

    @field_validator("work_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de la recolección")

    @model_validator(mode="after")
    def per_kg_needs_kg(self):
        if self.payment_type == HarvestPaymentTypeEnum.per_kg and self.kg_collected is None:
            raise ValueError("Indica los kg recogidos")
        return self


class HarvestWorkResponse(BaseModel):
    id: int
    harvest_id: int
    employee_id: int
    employee_name: str
    work_date: date
    payment_type: HarvestPaymentTypeEnum
    kg_collected: Optional[Decimal]
    rate_per_kg: Optional[Decimal]
    day_value: Optional[Decimal]
    total_value: Decimal
    paid: bool
    paid_at: Optional[date]
    created_at: datetime


class HarvestResponse(BaseModel):
    id: int
    crop_cycle_id: int
    cycle_number: int
    plot_id: int
    plot_name: str
    farm_id: int
    pass_number: int
    start_date: date
    end_date: Optional[date]
    status: HarvestStatusEnum
    rate_per_kg: Optional[Decimal]
    rate_per_day: Optional[Decimal]
    total_cherry_kg: Optional[Decimal]
    observations: Optional[str]
    created_at: datetime
    works_count: int
    kg_registered: Decimal = Field(..., description="Suma de los kg anotados en la recolección")
    value_total: Decimal = Field(..., description="Valor de toda la recolección")
    value_pending: Decimal = Field(..., description="Valor de la recolección sin pagar")


class HarvestDetail(HarvestResponse):
    works: List[HarvestWorkResponse]
