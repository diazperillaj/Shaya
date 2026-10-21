from datetime import date
from typing import Literal, Optional, List

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


# ─── Tablero del inventario ───────────────────────────────────────────────────

class InventoryLotProductResponse(BaseModel):
    detail_id: int
    product_id: int
    name: str
    # Existencia inicial del proceso + entradas por movimientos
    total_in: int
    # Ventas + ferias + salidas por movimientos
    total_out: int
    remaining_quantity: int
    unit_cost: Optional[float] = None


class InventoryLotResponse(BaseModel):
    id: int
    process_id: int
    invoice_number: str
    process_date: date
    variety: Optional[str] = None
    farmer_name: Optional[str] = None
    farm_name: Optional[str] = None
    altitude: Optional[float] = None
    yield_percentage: Optional[float] = None
    observations: Optional[str] = None
    products: List[InventoryLotProductResponse]


class InventoryEventResponse(BaseModel):
    """Entrada (+) o salida (−) de unidades de un producto de un lote."""

    event_date: date
    lot_id: int
    detail_id: int
    product_id: int
    product_name: str
    kind: Literal["process", "sale", "fair", "movement", "adjustment"]
    quantity: int
    reference: str
    note: Optional[str] = None


class RoastedInventoryDashboardResponse(BaseModel):
    lots: List[InventoryLotResponse]
    # Ordenados por fecha; por lote y producto suman su cantidad restante
    events: List[InventoryEventResponse]
