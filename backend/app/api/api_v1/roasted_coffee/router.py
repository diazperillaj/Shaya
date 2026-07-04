from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.roasted_coffee.schema import (
    RoastedCoffeeCreate,
    RoastedCoffeeDeleteResponse,
    RoastedCoffeeInventoryResponse,
    RoastedCoffeeUpdate,
)
from app.api.api_v1.roasted_coffee.service import RoastedCoffeeService
from app.core.db.session import get_db

router = APIRouter()


@router.get("/get", response_model=List[RoastedCoffeeInventoryResponse])
def get_maquilados(
    search: Optional[str] = Query(None, description="Buscar por nombre de producto o factura de proceso"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lista todos los registros de café maquilado."""
    return RoastedCoffeeService(db).get_roasted_coffees(search=search)


@router.get("/get/{maquilado_id}", response_model=RoastedCoffeeInventoryResponse)
def get_maquilado_by_id(
    maquilado_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Obtiene un maquilado por su ID."""
    return RoastedCoffeeService(db).get_roasted_coffee_by_id(maquilado_id)


@router.post("/create", response_model=RoastedCoffeeInventoryResponse)
def create_maquilado(
    payload: RoastedCoffeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Crea un maquilado manualmente asociado a un proceso existente.
    En condiciones normales se genera automáticamente al crear el proceso.
    """
    return RoastedCoffeeService(db).create_roasted_coffee(payload)


@router.put("/update/{maquilado_id}", response_model=RoastedCoffeeInventoryResponse)
def update_maquilado(
    maquilado_id: int,
    payload: RoastedCoffeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Actualiza observaciones y cantidades restantes de un maquilado.
    Cada cambio en remaining_quantity genera un movimiento de inventario.
    """
    return RoastedCoffeeService(db).update_roasted_coffee(maquilado_id, payload)


@router.delete("/delete/{maquilado_id}", response_model=RoastedCoffeeDeleteResponse)
def delete_maquilado(
    maquilado_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Elimina un maquilado y sus detalles.
    Normalmente se borra en cascada al eliminar el proceso.
    """
    return RoastedCoffeeService(db).delete_roasted_coffee(maquilado_id)
