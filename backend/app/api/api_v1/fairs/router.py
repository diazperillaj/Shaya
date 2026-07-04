from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.fairs.schema import (
    FairCreate,
    FairExpenseCreate,
    FairExpenseUpdate,
    FairInventoryCreate,
    FairInventoryUpdate,
    FairReportResponse,
    FairResponse,
    FairSaleCreate,
    FairSaleUpdate,
    FairUpdate,
)
from app.api.api_v1.fairs.service import FairService
from app.core.db.session import get_db

router = APIRouter()


# ─── Fairs CRUD ───────────────────────────────────────────────────────────────

@router.post("/create", response_model=FairResponse)
def create_fair(
    payload: FairCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).create_fair(payload, current_user)


@router.get("/get", response_model=List[FairResponse])
def get_fairs(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).get_fairs(search=search)


@router.get("/get/{fair_id}", response_model=FairResponse)
def get_fair_by_id(
    fair_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).get_fair_by_id(fair_id)


@router.put("/update/{fair_id}", response_model=FairResponse)
def update_fair(
    fair_id: int,
    payload: FairUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).update_fair(fair_id, payload, current_user)


@router.delete("/delete/{fair_id}", response_model=dict)
def delete_fair(
    fair_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not FairService(db).delete_fair(fair_id):
        raise HTTPException(status_code=404, detail="Feria no encontrada")
    return {"message": f"Feria {fair_id} eliminada exitosamente"}


@router.post("/{fair_id}/close", response_model=FairResponse)
def close_fair(
    fair_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).close_fair(fair_id, current_user)


@router.get("/{fair_id}/report", response_model=FairReportResponse)
def get_fair_report(
    fair_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).get_fair_report(fair_id)


# ─── Fair Inventory ───────────────────────────────────────────────────────────

@router.post("/{fair_id}/inventory/create", response_model=FairResponse)
def create_fair_inventory(
    fair_id: int,
    payload: FairInventoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).create_fair_inventory(fair_id, payload, current_user)


@router.put("/{fair_id}/inventory/{inv_id}", response_model=FairResponse)
def update_fair_inventory(
    fair_id: int,
    inv_id: int,
    payload: FairInventoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).update_fair_inventory(fair_id, inv_id, payload, current_user)


@router.delete("/{fair_id}/inventory/{inv_id}", response_model=FairResponse)
def delete_fair_inventory(
    fair_id: int,
    inv_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return FairService(db).delete_fair_inventory(fair_id, inv_id, current_user)


# ─── Fair Sales ───────────────────────────────────────────────────────────────

@router.post("/{fair_id}/sales/create", response_model=FairResponse)
def create_fair_sale(
    fair_id: int,
    payload: FairSaleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).create_fair_sale(fair_id, payload, current_user)


@router.put("/{fair_id}/sales/{sale_id}", response_model=FairResponse)
def update_fair_sale(
    fair_id: int,
    sale_id: int,
    payload: FairSaleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).update_fair_sale(fair_id, sale_id, payload, current_user)


@router.delete("/{fair_id}/sales/{sale_id}", response_model=FairResponse)
def delete_fair_sale(
    fair_id: int,
    sale_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return FairService(db).delete_fair_sale(fair_id, sale_id, current_user)


# ─── Fair Expenses ────────────────────────────────────────────────────────────

@router.post("/{fair_id}/expenses/create", response_model=FairResponse)
def create_fair_expense(
    fair_id: int,
    payload: FairExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).create_fair_expense(fair_id, payload, current_user)


@router.put("/{fair_id}/expenses/{expense_id}", response_model=FairResponse)
def update_fair_expense(
    fair_id: int,
    expense_id: int,
    payload: FairExpenseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairService(db).update_fair_expense(fair_id, expense_id, payload, current_user)


@router.delete("/{fair_id}/expenses/{expense_id}", response_model=FairResponse)
def delete_fair_expense(
    fair_id: int,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return FairService(db).delete_fair_expense(fair_id, expense_id, current_user)
