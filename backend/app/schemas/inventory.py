from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.schemas.product import ProductResponse


# =========================
# Schemas de entrada
# =========================

class InventoryCreate(BaseModel):
    """
    Esquema para crear un registro de inventario.

    Se usa en operaciones de entrada y valida los datos enviados por el cliente.
    """

    product_id: int
    date: datetime
    quantity: Decimal
    observations: Optional[str] = None


# =========================
# Schemas de salida
# =========================

class InventoryResponse(BaseModel):
    """
    Esquema para respuestas de la API relacionadas con inventario.
    """

    id: int
    product: ProductResponse
    date: datetime
    quantity: Decimal
    observations: Optional[str] = None

    class Config:
        from_attributes = True  # ✔ correcto para Pydantic v2