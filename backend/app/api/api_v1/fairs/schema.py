from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.fair import FairStatusEnum
from app.models.fair_expense import ExpenseCategoryEnum


# ─── Nested read-only sub-schemas ────────────────────────────────────────────

class PersonBasicResponse(BaseModel):
    id: int
    full_name: str
    model_config = ConfigDict(from_attributes=True)


class UserBasicResponse(BaseModel):
    id: int
    username: str
    role: str
    person: PersonBasicResponse
    model_config = ConfigDict(from_attributes=True)


class PaymentMethodBasicResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class ProductBasicResponse(BaseModel):
    id: int
    name: str
    quantity: int
    model_config = ConfigDict(from_attributes=True)


class DRCBasicResponse(BaseModel):
    id: int
    roasted_coffee_id: int
    product_id: int
    product: Optional[ProductBasicResponse] = None
    quantity: int
    remaining_quantity: int
    model_config = ConfigDict(from_attributes=True)


# ─── FairExpense schemas ──────────────────────────────────────────────────────

class FairExpenseCreate(BaseModel):
    category: str = Field(..., description="food | supplies | transport | other")
    description: str = Field(..., min_length=1, max_length=300)
    amount: Decimal = Field(..., gt=0)
    expense_datetime: Optional[datetime] = Field(default=None)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {e.value for e in ExpenseCategoryEnum}
        if v not in valid:
            raise ValueError(f"Categoría inválida. Opciones: {valid}")
        return v


class FairExpenseUpdate(FairExpenseCreate):
    pass


class FairExpenseResponse(BaseModel):
    id: int
    fair_id: int
    user_id: int
    user: Optional[UserBasicResponse] = None
    category: str
    description: str
    amount: Decimal
    expense_datetime: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "category") and isinstance(obj.category, ExpenseCategoryEnum):
            instance.category = obj.category.value
        return instance


# ─── FairInventory schemas ────────────────────────────────────────────────────

class FairInventoryCreate(BaseModel):
    detail_roasted_coffee_id: int = Field(..., gt=0)
    initial_quantity: int = Field(..., gt=0, description="Número de bolsas a asignar a la feria")
    unit_value: Decimal = Field(..., gt=0, description="Precio de referencia por bolsa")


class FairInventoryUpdate(BaseModel):
    initial_quantity: int = Field(..., gt=0)
    unit_value: Decimal = Field(..., gt=0)


class FairInventoryResponse(BaseModel):
    id: int
    fair_id: int
    detail_roasted_coffee_id: int
    detail_roasted_coffee: Optional[DRCBasicResponse] = None
    initial_quantity: int
    remaining_quantity: int
    unit_value: Decimal

    model_config = ConfigDict(from_attributes=True)


# ─── FairSale schemas ─────────────────────────────────────────────────────────

class FairSaleCreate(BaseModel):
    fair_inventory_id: int = Field(..., gt=0)
    payment_method_id: int = Field(..., gt=0, description="Método de pago (obligatorio)")
    quantity: int = Field(..., gt=0, description="Número de bolsas a vender")
    unit_value: Decimal = Field(..., gt=0, description="Precio de venta por bolsa")
    sale_datetime: Optional[datetime] = Field(default=None)
    observations: Optional[str] = Field(default=None, max_length=500)


class FairSaleUpdate(FairSaleCreate):
    pass


class FairSaleResponse(BaseModel):
    id: int
    fair_id: int
    fair_inventory_id: int
    fair_inventory: Optional[FairInventoryResponse] = None
    payment_method_id: int
    payment_method: Optional[PaymentMethodBasicResponse] = None
    sale_datetime: datetime
    quantity: int
    unit_value: Decimal
    total: Decimal
    observations: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Fair schemas ─────────────────────────────────────────────────────────────

class FairCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    start_datetime: datetime = Field(..., description="Fecha y hora de inicio de la feria")
    observations: Optional[str] = Field(default=None, max_length=1000)


class FairUpdate(FairCreate):
    pass


class FairResponse(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    status: str
    user_id: int
    user: Optional[UserBasicResponse] = None
    sale_id: Optional[int] = None
    observations: Optional[str] = None
    inventory: List[FairInventoryResponse] = []
    fair_sales: List[FairSaleResponse] = []
    expenses: List[FairExpenseResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "status") and isinstance(obj.status, FairStatusEnum):
            instance.status = obj.status.value
        return instance


# ─── Report schemas ───────────────────────────────────────────────────────────

class FairKPIs(BaseModel):
    total_sales: Decimal
    total_transactions: int
    avg_sale_value: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    margin_percentage: Decimal
    total_bags_assigned: int
    total_bags_sold: int
    total_bags_remaining: int
    inventory_utilization_percentage: Decimal
    duration_hours: Optional[float] = None


class ChartSeries(BaseModel):
    name: str
    data: List[float]


class BarChartData(BaseModel):
    labels: List[str]
    series: List[ChartSeries]


class PieChartData(BaseModel):
    labels: List[str]
    data: List[float]


class FairInventoryStatusItem(BaseModel):
    product_name: str
    detail_roasted_coffee_id: int
    initial_quantity: int
    sold_quantity: int
    remaining_quantity: int
    utilization_percentage: Decimal
    revenue: Decimal


class FairReportResponse(BaseModel):
    fair: FairResponse
    kpis: FairKPIs
    sales_by_product: BarChartData
    sales_timeline: BarChartData
    expenses_by_category: PieChartData
    inventory_status: List[FairInventoryStatusItem]
