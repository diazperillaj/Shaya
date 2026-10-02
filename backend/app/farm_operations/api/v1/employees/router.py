from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.employees.schema import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.farm_operations.api.v1.employees.service import EmployeeService
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> EmployeeService:
    return EmployeeService(db, access)


@router.post("/create", response_model=EmployeeResponse)
def create_employee(payload: EmployeeCreate, service: EmployeeService = Depends(get_service)):
    return service.create_employee(payload)


@router.get("/get", response_model=List[EmployeeResponse])
def get_employees(
    farm_id: Optional[int] = Query(None),
    active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Nombre o documento"),
    service: EmployeeService = Depends(get_service),
):
    return service.get_employees(farm_id=farm_id, active=active, search=search)


@router.put("/update/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, payload: EmployeeUpdate, service: EmployeeService = Depends(get_service)):
    return service.update_employee(employee_id, payload)


@router.post("/{employee_id}/deactivate", response_model=EmployeeResponse)
def deactivate_employee(employee_id: int, service: EmployeeService = Depends(get_service)):
    """Retira al empleado de los formularios sin borrar su historial de pagos."""
    return service.set_active(employee_id, False)


@router.post("/{employee_id}/activate", response_model=EmployeeResponse)
def activate_employee(employee_id: int, service: EmployeeService = Depends(get_service)):
    return service.set_active(employee_id, True)


@router.delete("/delete/{employee_id}", response_model=dict)
def delete_employee(employee_id: int, service: EmployeeService = Depends(get_service)):
    """Elimina un empleado sin pagos ni jornales registrados."""
    service.delete_employee(employee_id)
    return {"message": f"Empleado {employee_id} eliminado exitosamente"}
