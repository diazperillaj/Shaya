from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future

TEMPERATURE = {"ge": -10, "le": 50, "max_digits": 4, "decimal_places": 1}


class ClimateRecordUpdate(BaseModel):
    plot_id: Optional[int] = Field(None, gt=0, description="Vacío = aplica a toda la finca")
    record_date: date
    rainfall_mm: Optional[Decimal] = Field(None, ge=0, max_digits=6, decimal_places=1)
    temp_min_c: Optional[Decimal] = Field(None, **TEMPERATURE)
    temp_max_c: Optional[Decimal] = Field(None, **TEMPERATURE)
    observations: Optional[str] = Field(None, description="Granizada, vendaval, helada…")

    @field_validator("record_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha del registro")

    @model_validator(mode="after")
    def consistent_measures(self):
        measures = (self.rainfall_mm, self.temp_min_c, self.temp_max_c)
        if all(value is None for value in measures) and not (self.observations or "").strip():
            raise ValueError("Registra la lluvia, la temperatura o una observación")
        if (
            self.temp_min_c is not None
            and self.temp_max_c is not None
            and self.temp_min_c > self.temp_max_c
        ):
            raise ValueError("La temperatura mínima no puede ser mayor que la máxima")
        return self


class ClimateRecordCreate(ClimateRecordUpdate):
    farm_id: int = Field(..., gt=0)


class ClimateRecordResponse(BaseModel):
    id: int
    farm_id: int
    plot_id: Optional[int]
    plot_name: Optional[str]
    record_date: date
    rainfall_mm: Optional[Decimal]
    temp_min_c: Optional[Decimal]
    temp_max_c: Optional[Decimal]
    observations: Optional[str]
    created_at: datetime
