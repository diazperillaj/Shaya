from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.farm_operations.models.enums import SupplyTypeEnum


class SupplyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    supply_type: SupplyTypeEnum
    other_detail: Optional[str] = Field(None, max_length=150, description="Tipo, cuando es `other`")
    unit: str = Field("kg", min_length=1, max_length=20, description="kg, L, g, cc…")
    composition: Optional[str] = Field(
        None, max_length=255, description="Ingrediente activo o grado (ej. 25-4-24)"
    )

    @model_validator(mode="after")
    def other_needs_detail(self):
        if self.supply_type == SupplyTypeEnum.other and not (self.other_detail or "").strip():
            raise ValueError("Indica qué tipo de insumo es")
        return self


class SupplyCreate(SupplyBase):
    pass


class SupplyUpdate(SupplyBase):
    pass


class SupplyResponse(BaseModel):
    id: int
    name: str
    supply_type: SupplyTypeEnum
    other_detail: Optional[str]
    unit: str
    composition: Optional[str]
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
