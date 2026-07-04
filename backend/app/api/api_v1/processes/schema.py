from decimal import Decimal
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.api.api_v1.inventory.schema import ParchmentResponse
from app.schemas.product import ProductResponse


class ProcessDetailCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    bag_quantity: int = Field(..., gt=0)
    grams_per_bag: int = Field(..., gt=-1)
    unit_value: Decimal = Field(..., gt=0)
    observations: Optional[str] = None


class ProcessCreate(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=100)
    process_date: str
    parchment_id: int = Field(..., gt=0, description="ID del inventario de pergamino seco")
    parchment_kg: Decimal = Field(..., gt=0)
    observations: Optional[str] = None
    details: List[ProcessDetailCreate] = Field(..., min_length=1)


class ProcessUpdate(ProcessCreate):
    pass


class ProcessDetailResponse(BaseModel):
    id: int
    process_id: int
    date: date
    product_id: int
    product: Optional[ProductResponse] = None
    bag_quantity: int
    grams_per_bag: int
    unit_value: Decimal
    iva: Decimal
    total: Decimal
    observations: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessResponse(BaseModel):
    id: int
    invoice_number: str
    process_date: date
    parchment_id: int
    parchment_kg: Decimal
    resultant_kg: Decimal
    yield_percentage: Decimal
    subtotal: Decimal
    iva: Decimal
    total: Decimal
    observations: Optional[str] = None
    # Incluye inventario de pergamino seco usado en el proceso
    parchment: Optional[ParchmentResponse] = None
    details: List[ProcessDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)