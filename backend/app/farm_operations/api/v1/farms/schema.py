from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class FarmBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    village: str = Field(..., min_length=1, max_length=255, description="Vereda")
    municipality: str = Field(..., min_length=1, max_length=255)
    altitude: Optional[Decimal] = Field(
        None, ge=0, max_digits=6, decimal_places=2, description="m s.n.m."
    )
    total_area: Optional[Decimal] = Field(
        None, gt=0, max_digits=8, decimal_places=2, description="Hectáreas"
    )
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, max_digits=9, decimal_places=6)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, max_digits=9, decimal_places=6)
    observations: Optional[str] = None


class FarmCreate(FarmBase):
    farmer_id: Optional[int] = Field(
        None,
        gt=0,
        description="Obligatorio para administradores; un caficultor registra a su nombre",
    )


class FarmUpdate(FarmBase):
    active: bool = True


class FarmerSummary(BaseModel):
    id: int
    full_name: str


class FarmResponse(BaseModel):
    id: int
    farmer: FarmerSummary
    name: str
    village: str
    municipality: str
    altitude: Optional[Decimal]
    total_area: Optional[Decimal]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    active: bool
    observations: Optional[str]
    created_at: datetime
    active_plots: int
