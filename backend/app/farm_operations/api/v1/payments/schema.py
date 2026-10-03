from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future
from app.farm_operations.models.enums import HarvestPaymentTypeEnum, LaborActivityEnum
from app.farm_operations.services.dates import business_today


class PaymentItem(BaseModel):
    """Un trabajo por pagar o pagado: recolección de un día o un jornal."""

    kind: Literal["harvest_work", "day_labor"]
    id: int
    farm_id: int
    employee_id: int
    employee_name: str
    item_date: date
    amount: Decimal
    paid: bool
    paid_at: Optional[date]
    plot_name: Optional[str]
    # Recolección
    harvest_id: Optional[int] = None
    pass_number: Optional[int] = None
    payment_type: Optional[HarvestPaymentTypeEnum] = None
    kg_collected: Optional[Decimal] = None
    # Jornal
    activity_type: Optional[LaborActivityEnum] = None
    other_detail: Optional[str] = None


class PaymentSelection(BaseModel):
    harvest_work_ids: List[int] = Field(default_factory=list)
    day_labor_ids: List[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def something_selected(self):
        if not self.harvest_work_ids and not self.day_labor_ids:
            raise ValueError("Elige al menos un trabajo o jornal")
        return self


class PayRequest(PaymentSelection):
    paid_at: date = Field(default_factory=business_today)

    @field_validator("paid_at")
    @classmethod
    def paid_not_in_future(cls, value):
        return not_in_future(value, "La fecha de pago")


class PaymentResult(BaseModel):
    """Lo que cambió: cuántos trabajos y por cuánto dinero."""

    count: int
    total: Decimal
