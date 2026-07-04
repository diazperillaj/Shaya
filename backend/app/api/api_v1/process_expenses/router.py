from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.process_expenses.schema import (
    ProcessExpenseCreate,
    ProcessExpenseResponse,
    ProcessExpenseUpdate,
)
from app.api.api_v1.process_expenses.service import ProcessExpenseService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=ProcessExpenseResponse)
def create_process_expense(
    payload: ProcessExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crea un gasto de proceso y recalcula el costo de sus lotes."""
    return ProcessExpenseService(db).create_expense(payload, current_user)


@router.get("/get", response_model=List[ProcessExpenseResponse])
def get_process_expenses(
    process_id: Optional[int] = Query(None, description="Filtrar por proceso"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ProcessExpenseService(db).get_expenses(process_id=process_id)


@router.get("/get/{expense_id}", response_model=ProcessExpenseResponse)
def get_process_expense_by_id(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ProcessExpenseService(db).get_expense_by_id(expense_id)


@router.put("/update/{expense_id}", response_model=ProcessExpenseResponse)
def update_process_expense(
    expense_id: int,
    payload: ProcessExpenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Actualiza un gasto de proceso y recalcula el costo de sus lotes."""
    return ProcessExpenseService(db).update_expense(expense_id, payload)


@router.delete("/delete/{expense_id}", response_model=dict)
def delete_process_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Elimina un gasto de proceso y recalcula el costo de sus lotes."""
    if not ProcessExpenseService(db).delete_expense(expense_id):
        raise HTTPException(status_code=404, detail="Gasto de proceso no encontrado")
    return {"message": f"Gasto de proceso {expense_id} eliminado exitosamente"}
