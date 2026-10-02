from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import require_admin
from app.core.db.session import get_db
from app.farm_operations.api.v1.farmer_accounts.schema import (
    FarmerAccountCreate,
    FarmerAccountCreateFull,
    FarmerAccountResponse,
)
from app.farm_operations.api.v1.farmer_accounts.service import FarmerAccountService

# Solo administradores: no hay autoregistro de caficultores
router = APIRouter(dependencies=[Depends(require_admin)])


def get_service(db: Session = Depends(get_db)) -> FarmerAccountService:
    return FarmerAccountService(db)


@router.get("/get", response_model=List[FarmerAccountResponse])
def get_accounts(service: FarmerAccountService = Depends(get_service)):
    """Caficultores registrados y el estado de su acceso."""
    return service.get_accounts()


@router.post("/create", response_model=FarmerAccountResponse)
def create_account(payload: FarmerAccountCreate, service: FarmerAccountService = Depends(get_service)):
    """Da acceso a un caficultor ya registrado."""
    return service.create_account(payload)


@router.post("/create-full", response_model=FarmerAccountResponse)
def create_full_account(payload: FarmerAccountCreateFull, service: FarmerAccountService = Depends(get_service)):
    """Registra un caficultor nuevo con su cuenta, en una sola operación."""
    return service.create_full(payload)
