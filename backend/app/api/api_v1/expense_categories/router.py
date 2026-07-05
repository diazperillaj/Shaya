from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.expense_categories.schema import (
    ExpenseCategoryCreate,
    ExpenseCategoryResponse,
    ExpenseCategoryUpdate,
)
from app.api.api_v1.expense_categories.service import ExpenseCategoryService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=ExpenseCategoryResponse)
def create_expense_category(
    payload: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ExpenseCategoryService(db).create_category(payload)


@router.get("/get", response_model=List[ExpenseCategoryResponse])
def get_expense_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ExpenseCategoryService(db).get_categories()


@router.get("/get/{category_id}", response_model=ExpenseCategoryResponse)
def get_expense_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ExpenseCategoryService(db).get_category_by_id(category_id)


@router.put("/update/{category_id}", response_model=ExpenseCategoryResponse)
def update_expense_category(
    category_id: int,
    payload: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ExpenseCategoryService(db).update_category(category_id, payload)


@router.delete("/delete/{category_id}", response_model=dict)
def delete_expense_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not ExpenseCategoryService(db).delete_category(category_id):
        raise HTTPException(status_code=404, detail="Categoría de gasto no encontrada")
    return {"message": f"Categoría {category_id} eliminada exitosamente"}
