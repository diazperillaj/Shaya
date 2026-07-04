from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.sale import SaleStatusEnum


# ─── Nested read-only sub-schemas ────────────────────────────────────────────

class PersonBasicResponse(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class CustomerBasicResponse(BaseModel):
    id: int
    customerType: str
    city: str
    person: PersonBasicResponse

    model_config = ConfigDict(from_attributes=True)


class UserBasicResponse(BaseModel):
    id: int
    username: str
    role: str
    person: PersonBasicResponse

    model_config = ConfigDict(from_attributes=True)


class ProductBasicResponse(BaseModel):
    id: int
    name: str
    quantity: int  # grams per bag as defined in the catalog

    model_config = ConfigDict(from_attributes=True)


class DetailRoastedCoffeeBasicResponse(BaseModel):
    id: int
    roasted_coffee_id: int
    product_id: int
    product: Optional[ProductBasicResponse] = None
    quantity: int
    remaining_quantity: int

    model_config = ConfigDict(from_attributes=True)


# ─── Detail sale schemas ──────────────────────────────────────────────────────

class SaleDetailCreate(BaseModel):
    detail_roasted_coffee_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, description="Número de bolsas a vender")
    unit_value: Decimal = Field(..., gt=0, description="Precio por unidad (bolsa)")
    iva_percentage: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        description="Porcentaje de IVA aplicado a este ítem (ej: 10.5 → 10.5%)",
    )


class SaleDetailResponse(BaseModel):
    id: int
    sale_id: int
    detail_roasted_coffee_id: int
    detail_roasted_coffee: Optional[DetailRoastedCoffeeBasicResponse] = None
    quantity: int
    unit_value: Decimal
    iva_percentage: Decimal
    subtotal: Decimal
    iva: Decimal
    total: Decimal

    model_config = ConfigDict(from_attributes=True)


# ─── Sale schemas ─────────────────────────────────────────────────────────────

class SaleCreate(BaseModel):
    customer_id: Optional[int] = Field(default=None, gt=0)
    user_id: Optional[int] = Field(
        default=None,
        gt=0,
        description="Solo un admin puede asignar la venta a otro usuario",
    )
    sale_date: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    status: str = Field(default="in_progress")
    observations: Optional[str] = Field(default=None, max_length=500)
    details: List[SaleDetailCreate] = Field(..., min_length=1)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {e.value for e in SaleStatusEnum}
        if v not in valid:
            raise ValueError(f"Estado inválido. Opciones: {valid}")
        return v


class SaleUpdate(SaleCreate):
    pass


class SaleResponse(BaseModel):
    id: int
    customer_id: Optional[int] = None
    customer: Optional[CustomerBasicResponse] = None
    user_id: int
    user: Optional[UserBasicResponse] = None
    sale_date: date
    status: str
    observations: Optional[str] = None
    subtotal: Decimal
    iva: Decimal
    total: Decimal
    details: List[SaleDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Serialize the SQLAlchemy enum to its string value for the response
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "status") and isinstance(obj.status, SaleStatusEnum):
            instance.status = obj.status.value
        return instance
