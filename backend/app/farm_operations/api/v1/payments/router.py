from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.payments.schema import (
    PayRequest,
    PaymentItem,
    PaymentResult,
    PaymentSelection,
)
from app.farm_operations.api.v1.payments.service import PaymentService
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> PaymentService:
    return PaymentService(db, access)


@router.get("/get", response_model=List[PaymentItem])
def get_items(
    farm_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    paid: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: PaymentService = Depends(get_service),
):
    """Recolección y jornales por empleado; con `paid=false`, lo pendiente de pago."""
    return service.get_items(
        farm_id=farm_id, employee_id=employee_id, paid=paid, date_from=date_from, date_to=date_to,
    )


@router.post("/pay", response_model=PaymentResult)
def pay(payload: PayRequest, service: PaymentService = Depends(get_service)):
    """Paga los trabajos y jornales elegidos, en una sola transacción."""
    return service.pay(payload)


@router.post("/unpay", response_model=PaymentResult)
def unpay(payload: PaymentSelection, service: PaymentService = Depends(get_service)):
    """Deshace pagos marcados por error."""
    return service.unpay(payload)
