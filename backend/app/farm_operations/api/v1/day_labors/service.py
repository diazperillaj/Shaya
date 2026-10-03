from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.api.v1.day_labors.schema import DayLaborFields
from app.farm_operations.api.v1.validation import clean_other_detail
from app.farm_operations.models import DayLabor, Employee
from app.farm_operations.models.enums import LaborActivityEnum, PlotStatusEnum
from app.farm_operations.services.access import FarmAccess


class DayLaborService:
    """
    Jornales: días de trabajo pagados que no son recolección.

    Cuelgan del empleado; el lote es opcional y debe ser de la misma finca.
    Un jornal pagado no se modifica ni se elimina (primero se deshace el
    pago).
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_labors(
        self,
        farm_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        paid: Optional[bool] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[dict]:
        query = self.access.day_labors()
        if farm_id is not None:
            query = query.filter(Employee.farm_id == farm_id)
        if employee_id is not None:
            query = query.filter(DayLabor.employee_id == employee_id)
        if plot_id is not None:
            query = query.filter(DayLabor.plot_id == plot_id)
        if paid is not None:
            query = query.filter(DayLabor.paid == paid)
        if date_from is not None:
            query = query.filter(DayLabor.labor_date >= date_from)
        if date_to is not None:
            query = query.filter(DayLabor.labor_date <= date_to)
        labors = query.order_by(DayLabor.labor_date.desc(), DayLabor.id.desc()).all()
        return [labor_response(labor) for labor in labors]

    def create(self, payload: DayLaborFields) -> dict:
        labor = DayLabor()
        self._fill(labor, payload)
        self.db.add(labor)
        self.db.commit()
        self.db.refresh(labor)
        return labor_response(labor)

    def update(self, labor_id: int, payload: DayLaborFields) -> dict:
        labor = self.access.get_day_labor(labor_id)
        if labor.paid:
            raise ConflictError("Un jornal pagado no se modifica: deshaz el pago primero")
        self._fill(labor, payload)
        self.db.commit()
        self.db.refresh(labor)
        return labor_response(labor)

    def delete(self, labor_id: int) -> None:
        labor = self.access.get_day_labor(labor_id)
        if labor.paid:
            raise ConflictError("Un jornal pagado no se elimina: deshaz el pago primero")
        self.db.delete(labor)
        self.db.commit()

    def _fill(self, labor: DayLabor, payload: DayLaborFields) -> None:
        employee = self.access.get_employee(payload.employee_id)
        if not employee.active and employee.id != labor.employee_id:
            raise ConflictError(f"{employee.full_name} está inactivo: actívalo para registrarle jornales")

        if payload.plot_id is not None:
            plot = self.access.get_plot(payload.plot_id)
            if plot.farm_id != employee.farm_id:
                raise ConflictError("El lote no es de la finca del empleado")
            if plot.status == PlotStatusEnum.closed and plot.id != labor.plot_id:
                raise ConflictError(f"El lote «{plot.name}» está cerrado: no admite registros nuevos")

        is_other = payload.activity_type == LaborActivityEnum.other
        labor.employee_id = employee.id
        labor.labor_date = payload.labor_date
        labor.activity_type = payload.activity_type
        labor.other_detail = clean_other_detail(is_other, payload.other_detail)
        labor.plot_id = payload.plot_id
        labor.daily_value = payload.daily_value
        labor.observations = (payload.observations or "").strip() or None


def labor_response(labor: DayLabor) -> dict:
    return {
        "id": labor.id,
        "employee_id": labor.employee_id,
        "employee_name": labor.employee.full_name,
        "farm_id": labor.employee.farm_id,
        "labor_date": labor.labor_date,
        "activity_type": labor.activity_type,
        "other_detail": labor.other_detail,
        "plot_id": labor.plot_id,
        "plot_name": labor.plot.name if labor.plot else None,
        "daily_value": labor.daily_value,
        "paid": labor.paid,
        "paid_at": labor.paid_at,
        "observations": labor.observations,
        "created_at": labor.created_at,
    }
