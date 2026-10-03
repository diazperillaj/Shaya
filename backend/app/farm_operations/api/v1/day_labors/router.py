from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.day_labors.schema import DayLaborFields, DayLaborResponse
from app.farm_operations.api.v1.day_labors.service import DayLaborService
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> DayLaborService:
    return DayLaborService(db, access)


@router.post("/create", response_model=DayLaborResponse)
def create_labor(payload: DayLaborFields, service: DayLaborService = Depends(get_service)):
    """Registra un jornal: empleado, actividad, lote opcional y valor del día."""
    return service.create(payload)


@router.get("/get", response_model=List[DayLaborResponse])
def get_labors(
    farm_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    plot_id: Optional[int] = Query(None),
    paid: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: DayLaborService = Depends(get_service),
):
    return service.get_labors(
        farm_id=farm_id, employee_id=employee_id, plot_id=plot_id,
        paid=paid, date_from=date_from, date_to=date_to,
    )


@router.put("/update/{labor_id}", response_model=DayLaborResponse)
def update_labor(labor_id: int, payload: DayLaborFields, service: DayLaborService = Depends(get_service)):
    """Corrige un jornal sin pagar."""
    return service.update(labor_id, payload)


@router.delete("/delete/{labor_id}", response_model=dict)
def delete_labor(labor_id: int, service: DayLaborService = Depends(get_service)):
    """Elimina un jornal sin pagar."""
    service.delete(labor_id)
    return {"message": f"Jornal {labor_id} eliminado exitosamente"}
