from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.product_expense import ProductExpenseCategoryEnum


class ProductExpenseCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    category: str = Field(..., description="packaging | label | supplies | other")
    amount: Decimal = Field(..., gt=0, description="Valor POR BOLSA")
    observations: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {e.value for e in ProductExpenseCategoryEnum}
        if v not in valid:
            raise ValueError(f"Categoría inválida. Opciones: {valid}")
        return v


class ProductExpenseUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    observations: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {e.value for e in ProductExpenseCategoryEnum}
        if v not in valid:
            raise ValueError(f"Categoría inválida. Opciones: {valid}")
        return v


class ProductExpenseResponse(BaseModel):
    id: int
    product_id: int
    category: str
    amount: Decimal
    observations: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "category") and isinstance(
            obj.category, ProductExpenseCategoryEnum
        ):
            instance.category = obj.category.value
        return instance
