from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCategoryBasicResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PaymentMethodBasicResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GeneralExpenseCreate(BaseModel):
    expense_date: date
    amount: Decimal = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    payment_method_id: Optional[int] = Field(default=None, gt=0)
    description: str = Field(..., min_length=1, max_length=500, description="Motivo del gasto")


class GeneralExpenseUpdate(BaseModel):
    expense_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    category_id: Optional[int] = Field(None, gt=0)
    payment_method_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    # Permite quitar el método de pago explícitamente (es opcional en gastos)
    clear_payment_method: bool = False


class GeneralExpenseResponse(BaseModel):
    id: int
    expense_date: date
    amount: Decimal
    category_id: int
    category: Optional[ExpenseCategoryBasicResponse] = None
    payment_method_id: Optional[int] = None
    payment_method: Optional[PaymentMethodBasicResponse] = None
    description: str
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
