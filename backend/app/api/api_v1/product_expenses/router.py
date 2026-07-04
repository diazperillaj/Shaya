from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.product_expenses.schema import (
    ProductExpenseCreate,
    ProductExpenseResponse,
    ProductExpenseUpdate,
)
from app.api.api_v1.product_expenses.service import ProductExpenseService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=ProductExpenseResponse)
def create_product_expense(
    payload: ProductExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crea un costo de producción por bolsa (aplica a procesos futuros)."""
    return ProductExpenseService(db).create_expense(payload)


@router.get("/get", response_model=List[ProductExpenseResponse])
def get_product_expenses(
    product_id: Optional[int] = Query(None, description="Filtrar por producto"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ProductExpenseService(db).get_expenses(product_id=product_id)


@router.get("/get/{expense_id}", response_model=ProductExpenseResponse)
def get_product_expense_by_id(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ProductExpenseService(db).get_expense_by_id(expense_id)


@router.put("/update/{expense_id}", response_model=ProductExpenseResponse)
def update_product_expense(
    expense_id: int,
    payload: ProductExpenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ProductExpenseService(db).update_expense(expense_id, payload)


@router.delete("/delete/{expense_id}", response_model=dict)
def delete_product_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not ProductExpenseService(db).delete_expense(expense_id):
        raise HTTPException(status_code=404, detail="Costo de producción no encontrado")
    return {"message": f"Costo de producción {expense_id} eliminado exitosamente"}
