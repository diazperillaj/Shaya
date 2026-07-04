from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.process_expense import ProcessExpenseCategoryEnum


class ProcessExpenseCreate(BaseModel):
    process_id: int = Field(..., gt=0)
    category: str = Field(..., description="transport | labor | supplies | other")
    amount: Decimal = Field(..., gt=0, description="Valor TOTAL del gasto")
    expense_date: date
    observations: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {e.value for e in ProcessExpenseCategoryEnum}
        if v not in valid:
            raise ValueError(f"Categoría inválida. Opciones: {valid}")
        return v


class ProcessExpenseUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    observations: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = {e.value for e in ProcessExpenseCategoryEnum}
        if v not in valid:
            raise ValueError(f"Categoría inválida. Opciones: {valid}")
        return v


class ProcessExpenseResponse(BaseModel):
    id: int
    process_id: int
    category: str
    amount: Decimal
    expense_date: date
    observations: Optional[str] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "category") and isinstance(
            obj.category, ProcessExpenseCategoryEnum
        ):
            instance.category = obj.category.value
        return instance
