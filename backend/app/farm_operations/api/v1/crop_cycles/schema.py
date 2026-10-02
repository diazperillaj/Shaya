from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future
from app.farm_operations.models.enums import CycleStatusEnum
from app.farm_operations.services.dates import business_today


class CycleCreate(BaseModel):
    plot_id: int = Field(..., gt=0)
    start_date: date = Field(default_factory=business_today)
    observations: Optional[str] = None

    @field_validator("start_date")
    @classmethod
    def start_not_in_future(cls, value):
        return not_in_future(value, "La fecha de inicio")


class CycleUpdate(BaseModel):
    start_date: date
    end_date: Optional[date] = Field(None, description="Solo en ciclos cerrados")
    observations: Optional[str] = None

    @field_validator("start_date")
    @classmethod
    def start_not_in_future(cls, value):
        return not_in_future(value, "La fecha de inicio")

    @field_validator("end_date")
    @classmethod
    def end_not_in_future(cls, value):
        return not_in_future(value, "La fecha de fin")

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        return self


class CycleCloseRequest(BaseModel):
    end_date: date = Field(default_factory=business_today)

    @field_validator("end_date")
    @classmethod
    def end_not_in_future(cls, value):
        return not_in_future(value, "La fecha de fin")


class CycleResponse(BaseModel):
    id: int
    plot_id: int
    plot_name: str
    farm_id: int
    cycle_number: int
    start_date: date
    end_date: Optional[date]
    status: CycleStatusEnum
    observations: Optional[str]
    created_at: datetime


class RecordSummary(BaseModel):
    """Labores de un tipo dentro del ciclo."""

    kind: str = Field(..., description="Tipo de labor, como en su ruta: `fertilizations`…")
    count: int
    last_date: Optional[date]
    total_cost: Optional[Decimal] = Field(None, description="Solo en labores con costo")


class CycleDetail(CycleResponse):
    summary: List[RecordSummary]
