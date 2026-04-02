from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ProductCreate(BaseModel):
    """
    Esquema para crear un producto.
    """

    name: str
    type: str
    description: Optional[str] = None
    active: Optional[bool] = True

class ProductResponse(BaseModel):
    """
    Esquema de respuesta para productos.
    """

    id: int
    name: str
    type: str
    description: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True