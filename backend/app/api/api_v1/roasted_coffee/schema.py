from typing import Optional, List

from pydantic import BaseModel, Field


class DetailRoastedCoffeeCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class RoastedCoffeeCreate(BaseModel):
    process_id: int = Field(..., gt=0)
    observations: Optional[str] = None
    details: List[DetailRoastedCoffeeCreate]


class DetailRoastedCoffeeResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    remaining_quantity: int

    model_config = {"from_attributes": True}


class RoastedCoffeeResponse(BaseModel):
    id: int
    process_id: int
    observations: Optional[str] = None
    details: List[DetailRoastedCoffeeResponse]

    model_config = {"from_attributes": True}


class DetailRoastedCoffeeUpdate(BaseModel):
    id: int = Field(..., gt=0)
    remaining_quantity: int = Field(..., ge=0)


class RoastedCoffeeUpdate(BaseModel):
    observations: Optional[str] = None
    details: List[DetailRoastedCoffeeUpdate]


class RoastedCoffeeProductResponse(BaseModel):
    detail_id: int
    product_id: int
    name: str
    quantity: int
    remaining_quantity: int


class RoastedCoffeeInventoryResponse(BaseModel):
    id: int
    process_id: int
    variety: Optional[str] = None
    observations: Optional[str] = None
    products: List[RoastedCoffeeProductResponse]


class RoastedCoffeeDeleteResponse(BaseModel):
    message: str
