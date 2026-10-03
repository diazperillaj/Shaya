from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.api.v1.employees.schema import EmployeeCreate, EmployeeUpdate
from app.farm_operations.models import DayLabor, Employee, HarvestWork
from app.farm_operations.services.access import FarmAccess


def clean(value: Optional[str]) -> Optional[str]:
    return (value or "").strip() or None


class EmployeeService:
    """Trabajadores de las fincas, siempre dentro del alcance del usuario."""

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_employees(
        self,
        farm_id: Optional[int] = None,
        active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Employee]:
        query = self.access.employees()
        if farm_id is not None:
            query = query.filter(Employee.farm_id == farm_id)
        if active is not None:
            query = query.filter(Employee.active == active)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(or_(Employee.full_name.ilike(pattern), Employee.document.ilike(pattern)))
        return query.order_by(Employee.active.desc(), Employee.full_name).all()

    def create_employee(self, payload: EmployeeCreate) -> Employee:
        farm = self.access.get_farm(payload.farm_id)
        employee = Employee(farm_id=farm.id, **self._fields(payload))
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def update_employee(self, employee_id: int, payload: EmployeeUpdate) -> Employee:
        employee = self.access.get_employee(employee_id)
        for field, value in self._fields(payload).items():
            setattr(employee, field, value)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def set_active(self, employee_id: int, active: bool) -> Employee:
        employee = self.access.get_employee(employee_id)
        employee.active = active
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def delete_employee(self, employee_id: int) -> None:
        """Elimina un empleado sin historial; con recolección o jornales, se desactiva."""
        employee = self.access.get_employee(employee_id)
        for model in (HarvestWork, DayLabor):
            if self.db.query(model.id).filter(model.employee_id == employee.id).first():
                raise ConflictError("No se puede eliminar: tiene recolección o jornales registrados. Desactívalo")
        self.db.delete(employee)
        self.db.commit()

    @staticmethod
    def _fields(payload) -> dict:
        return {
            "full_name": payload.full_name.strip(),
            "document": clean(payload.document),
            "phone": clean(payload.phone),
            "observations": clean(payload.observations),
        }
