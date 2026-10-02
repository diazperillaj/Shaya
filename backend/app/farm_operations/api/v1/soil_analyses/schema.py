from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future

NUTRIENT = {"ge": 0, "max_digits": 8, "decimal_places": 2}
RESULTS = ("ph", "organic_matter_pct", "nitrogen", "phosphorus", "potassium", "texture")


class SoilAnalysisUpdate(BaseModel):
    analysis_date: date
    ph: Optional[Decimal] = Field(None, ge=0, le=14, max_digits=4, decimal_places=2)
    organic_matter_pct: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    nitrogen: Optional[Decimal] = Field(None, description="ppm o meq según el laboratorio", **NUTRIENT)
    phosphorus: Optional[Decimal] = Field(None, description="ppm o meq según el laboratorio", **NUTRIENT)
    potassium: Optional[Decimal] = Field(None, description="ppm o meq según el laboratorio", **NUTRIENT)
    texture: Optional[str] = Field(None, max_length=100)
    laboratory: Optional[str] = Field(None, max_length=150)
    observations: Optional[str] = None

    @field_validator("analysis_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha del análisis")

    @model_validator(mode="after")
    def has_a_result(self):
        values = [getattr(self, field) for field in RESULTS]
        if all(value is None or (isinstance(value, str) and not value.strip()) for value in values):
            raise ValueError("Registra al menos un resultado del análisis")
        return self


class SoilAnalysisCreate(SoilAnalysisUpdate):
    plot_id: int = Field(..., gt=0)


class SoilAnalysisResponse(BaseModel):
    id: int
    plot_id: int
    plot_name: str
    analysis_date: date
    ph: Optional[Decimal]
    organic_matter_pct: Optional[Decimal]
    nitrogen: Optional[Decimal]
    phosphorus: Optional[Decimal]
    potassium: Optional[Decimal]
    texture: Optional[str]
    laboratory: Optional[str]
    observations: Optional[str]
    created_at: datetime
