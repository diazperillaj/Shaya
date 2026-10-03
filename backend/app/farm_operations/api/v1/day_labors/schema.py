from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future, require_other_detail
from app.farm_operations.models.enums import LaborActivityEnum
from app.farm_operations.services.dates import business_today


class DayLaborFields(BaseModel):
    employee_id: int = Field(..., gt=0)
    labor_date: date = Field(default_factory=business_today)
    activity_type: LaborActivityEnum
    other_detail: Optional[str] = Field(None, max_length=150, description="Cuál actividad, cuando es `other`")
    plot_id: Optional[int] = Field(None, gt=0, description="Lote donde trabajó (opcional)")
    daily_value: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    observations: Optional[str] = None

    @field_validator("labor_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha del jornal")

    @model_validator(mode="after")
    def other_needs_detail(self):
        require_other_detail(
            self.activity_type == LaborActivityEnum.other, self.other_detail, "Indica cuál actividad es"
        )
        return self


class DayLaborResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    farm_id: int
    labor_date: date
    activity_type: LaborActivityEnum
    other_detail: Optional[str]
    plot_id: Optional[int]
    plot_name: Optional[str]
    daily_value: Decimal
    paid: bool
    paid_at: Optional[date]
    observations: Optional[str]
    created_at: datetime
