from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.user import UserResponse
from app.schemas.product import ProductResponse


class FastSaleCreate(BaseModel):
    product_id: int
    quantity: int
    price: float
    user_id: int
    description: Optional[str] = None

    @field_validator("description", mode="before")
    def empty_to_none(cls, v):
        return None if v == "" else v


class FastSaleResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    price: float
    user: UserResponse
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FastSaleUpdate(BaseModel):
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    user_id: Optional[int] = None
    description: Optional[str] = None

    @field_validator("description", mode="before")
    def empty_to_none(cls, v):
        return None if v == "" else v


class FastSaleUpdateResponse(BaseModel):
    """
    Mantiene consistencia con FastSaleResponse
    """
    id: int
    product: ProductResponse
    quantity: int
    price: float
    user: UserResponse
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)