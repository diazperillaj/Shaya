from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.sales.schema import SaleCreate, SaleResponse, SaleUpdate
from app.api.api_v1.sales.service import SaleService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=SaleResponse)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = SaleService(db)
    return service.create_sale(payload, current_user)


@router.get("/get", response_model=List[SaleResponse])
def get_sales(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = SaleService(db)
    return service.get_sales(search=search)


@router.get("/get/{sale_id}", response_model=SaleResponse)
def get_sale_by_id(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = SaleService(db)
    return service.get_sale_by_id(sale_id)


@router.put("/update/{sale_id}", response_model=SaleResponse)
def update_sale(
    sale_id: int,
    payload: SaleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = SaleService(db)
    return service.update_sale(sale_id, payload, current_user)


@router.delete("/delete/{sale_id}", response_model=dict)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    service = SaleService(db)
    if not service.delete_sale(sale_id):
        raise HTTPException(status_code=404, detail="Sale not found")
    return {"message": f"Sale {sale_id} deleted successfully"}
