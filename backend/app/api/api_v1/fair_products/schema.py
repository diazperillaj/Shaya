from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FairProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    default_price: Decimal = Field(..., gt=0, description="Precio de venta por defecto")


class FairProductUpdate(FairProductCreate):
    pass


class FairProductResponse(BaseModel):
    id: int
    name: str
    default_price: Decimal

    model_config = ConfigDict(from_attributes=True)
