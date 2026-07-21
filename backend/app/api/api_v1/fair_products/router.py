from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.fair_products.schema import (
    FairProductCreate,
    FairProductResponse,
    FairProductUpdate,
)
from app.api.api_v1.fair_products.service import FairProductService
from app.core.db.session import get_db

router = APIRouter()


@router.post("/create", response_model=FairProductResponse)
def create_fair_product(
    payload: FairProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairProductService(db).create_product(payload)


@router.get("/get", response_model=List[FairProductResponse])
def get_fair_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairProductService(db).get_products()


@router.get("/get/{product_id}", response_model=FairProductResponse)
def get_fair_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairProductService(db).get_product_by_id(product_id)


@router.put("/update/{product_id}", response_model=FairProductResponse)
def update_fair_product(
    product_id: int,
    payload: FairProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return FairProductService(db).update_product(product_id, payload)


@router.delete("/delete/{product_id}", response_model=dict)
def delete_fair_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not FairProductService(db).delete_product(product_id):
        raise HTTPException(status_code=404, detail="Producto de feria no encontrado")
    return {"message": f"Producto de feria {product_id} eliminado exitosamente"}
