from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.payment_methods.schema import (
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodUpdate,
)
from app.api.api_v1.payment_methods.service import PaymentMethodService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=PaymentMethodResponse)
def create_payment_method(
    payload: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PaymentMethodService(db).create_method(payload)


@router.get("/get", response_model=List[PaymentMethodResponse])
def get_payment_methods(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PaymentMethodService(db).get_methods()


@router.get("/get/{method_id}", response_model=PaymentMethodResponse)
def get_payment_method_by_id(
    method_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PaymentMethodService(db).get_method_by_id(method_id)


@router.put("/update/{method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    method_id: int,
    payload: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return PaymentMethodService(db).update_method(method_id, payload)


@router.delete("/delete/{method_id}", response_model=dict)
def delete_payment_method(
    method_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not PaymentMethodService(db).delete_method(method_id):
        raise HTTPException(status_code=404, detail="Método de pago no encontrado")
    return {"message": f"Método de pago {method_id} eliminado exitosamente"}
