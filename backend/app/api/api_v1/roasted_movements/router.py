from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.roasted_movements.schema import (
    RoastedMovementCreate,
    RoastedMovementResponse,
)
from app.api.api_v1.roasted_movements.service import RoastedMovementService
from app.core.db.session import get_db

router = APIRouter()


@router.get("/get", response_model=List[RoastedMovementResponse])
def get_movements(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return RoastedMovementService(db).get_movements()


@router.post("/create", response_model=RoastedMovementResponse)
def create_movement(
    payload: RoastedMovementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return RoastedMovementService(db).create_movement(payload, current_user)


@router.delete("/delete/{movement_id}", response_model=dict)
def delete_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if not RoastedMovementService(db).delete_movement(movement_id):
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    return {"message": f"Movimiento {movement_id} eliminado correctamente"}
