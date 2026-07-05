from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.general_expenses.schema import (
    GeneralExpenseCreate,
    GeneralExpenseResponse,
    GeneralExpenseUpdate,
)
from app.api.api_v1.general_expenses.service import GeneralExpenseService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=GeneralExpenseResponse)
def create_general_expense(
    payload: GeneralExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return GeneralExpenseService(db).create_expense(payload, current_user)


@router.get("/get", response_model=List[GeneralExpenseResponse])
def get_general_expenses(
    search: Optional[str] = Query(None, description="Buscar en el motivo"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    payment_method_id: Optional[int] = Query(
        None, description="Filtrar por método de pago"
    ),
    date_from: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return GeneralExpenseService(db).get_expenses(
        search=search,
        category_id=category_id,
        payment_method_id=payment_method_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/get/{expense_id}", response_model=GeneralExpenseResponse)
def get_general_expense_by_id(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return GeneralExpenseService(db).get_expense_by_id(expense_id)


@router.put("/update/{expense_id}", response_model=GeneralExpenseResponse)
def update_general_expense(
    expense_id: int,
    payload: GeneralExpenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return GeneralExpenseService(db).update_expense(expense_id, payload)


@router.delete("/delete/{expense_id}", response_model=dict)
def delete_general_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not GeneralExpenseService(db).delete_expense(expense_id):
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return {"message": f"Gasto {expense_id} eliminado exitosamente"}
