from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class RoastedMovementDetailCreate(BaseModel):
    """
    Línea de un movimiento de inventario maquilado.

    - Salida ("exit"): requiere detail_roasted_coffee_id (lote existente).
    - Entrada ("entry") a lote existente: detail_roasted_coffee_id.
    - Entrada ("entry") de producto nuevo: product_id (el lote se crea).
      · En reempaque el lote nuevo nace bajo el maquilado del lote origen.
      · En entrada pura requiere roasted_coffee_id (maquilado destino)
        y admite manual_unit_cost opcional.
    - grams_per_bag: obligatorio en entradas de reempaque, para repartir
      el valor de lo sacado proporcionalmente al peso.
    """

    detail_roasted_coffee_id: Optional[int] = Field(None, gt=0)
    product_id: Optional[int] = Field(None, gt=0)
    roasted_coffee_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(..., gt=0)
    grams_per_bag: Optional[int] = Field(None, gt=0)
    manual_unit_cost: Optional[Decimal] = Field(None, gt=0)
    # "exit" descuenta del inventario (envios, salidas);
    # "entry" agrega al inventario (reempaque, ajustes positivos)
    direction: Literal["entry", "exit"] = "exit"

    @model_validator(mode="after")
    def validate_line(self):
        if self.direction == "exit":
            if not self.detail_roasted_coffee_id:
                raise ValueError("Las salidas requieren un lote existente")
            if self.product_id:
                raise ValueError("Las salidas no admiten product_id")
        else:
            if not self.detail_roasted_coffee_id and not self.product_id:
                raise ValueError(
                    "Las entradas requieren un lote existente o un producto nuevo"
                )
            if self.detail_roasted_coffee_id and self.product_id:
                raise ValueError(
                    "Usa lote existente O producto nuevo, no ambos"
                )
        return self


class RoastedMovementCreate(BaseModel):
    movement_date: datetime
    observations: Optional[str] = None
    details: List[RoastedMovementDetailCreate] = Field(..., min_length=1)


class RoastedMovementDetailResponse(BaseModel):
    id: int
    detail_roasted_coffee_id: int
    roasted_coffee_id: int
    product_name: str
    quantity: int
    direction: Literal["entry", "exit"] = "exit"
    created_lot: bool = False

    model_config = {"from_attributes": True}


class RoastedMovementResponse(BaseModel):
    id: int
    movement_date: datetime
    observations: Optional[str] = None
    created_by: Optional[int] = None
    details: List[RoastedMovementDetailResponse]

    model_config = {"from_attributes": True}
