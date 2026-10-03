from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError, NotFoundError
from app.farm_operations.api.v1.payments.schema import PayRequest, PaymentSelection
from app.farm_operations.models import DayLabor, Employee, HarvestWork, Plot
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.dates import format_date


class PaymentService:
    """
    Pagos a los trabajadores: la recolección de cada día y los jornales.

    Se consultan juntos, por empleado, y se pagan por selección en una sola
    transacción. Deshacer un pago corrige una marca hecha por error.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_items(
        self,
        farm_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        paid: Optional[bool] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[dict]:
        works = self.access.harvest_works()
        labors = self.access.day_labors()
        if farm_id is not None:
            works = works.filter(Plot.farm_id == farm_id)
            labors = labors.filter(Employee.farm_id == farm_id)
        if employee_id is not None:
            works = works.filter(HarvestWork.employee_id == employee_id)
            labors = labors.filter(DayLabor.employee_id == employee_id)
        if paid is not None:
            works = works.filter(HarvestWork.paid == paid)
            labors = labors.filter(DayLabor.paid == paid)
        if date_from is not None:
            works = works.filter(HarvestWork.work_date >= date_from)
            labors = labors.filter(DayLabor.labor_date >= date_from)
        if date_to is not None:
            works = works.filter(HarvestWork.work_date <= date_to)
            labors = labors.filter(DayLabor.labor_date <= date_to)

        items = [work_item(work) for work in works.all()] + [labor_item(labor) for labor in labors.all()]
        return sorted(items, key=lambda item: (item["employee_name"], item["item_date"], item["kind"], item["id"]))

    def pay(self, payload: PayRequest) -> dict:
        """Marca como pagados los trabajos elegidos que estén pendientes."""
        changed = []
        for item, item_date in self._selected(payload):
            if item.paid:
                continue
            if payload.paid_at < item_date:
                raise ConflictError(
                    f"La fecha de pago no puede ser anterior al trabajo del {format_date(item_date)}"
                )
            item.paid, item.paid_at = True, payload.paid_at
            changed.append(item)
        self.db.commit()
        return summary(changed)

    def unpay(self, payload: PaymentSelection) -> dict:
        """Deshace pagos marcados por error: los trabajos vuelven a quedar pendientes."""
        changed = []
        for item, _ in self._selected(payload):
            if item.paid:
                item.paid, item.paid_at = False, None
                changed.append(item)
        self.db.commit()
        return summary(changed)

    def _selected(self, payload: PaymentSelection) -> list:
        """Trabajos y jornales elegidos, con su fecha; todos dentro del alcance."""
        work_ids, labor_ids = set(payload.harvest_work_ids), set(payload.day_labor_ids)
        works = self.access.harvest_works().filter(HarvestWork.id.in_(work_ids)).all() if work_ids else []
        labors = self.access.day_labors().filter(DayLabor.id.in_(labor_ids)).all() if labor_ids else []
        if len(works) != len(work_ids) or len(labors) != len(labor_ids):
            raise NotFoundError("Algún trabajo elegido no existe o no es de tus fincas")
        return [(work, work.work_date) for work in works] + [(labor, labor.labor_date) for labor in labors]


def amount_of(item) -> Decimal:
    return item.total_value if isinstance(item, HarvestWork) else item.daily_value


def summary(items: list) -> dict:
    return {"count": len(items), "total": sum((amount_of(item) for item in items), Decimal(0))}


def work_item(work: HarvestWork) -> dict:
    harvest = work.harvest
    plot = harvest.crop_cycle.plot
    return {
        "kind": "harvest_work",
        "id": work.id,
        "farm_id": plot.farm_id,
        "employee_id": work.employee_id,
        "employee_name": work.employee.full_name,
        "item_date": work.work_date,
        "amount": work.total_value,
        "paid": work.paid,
        "paid_at": work.paid_at,
        "plot_name": plot.name,
        "harvest_id": harvest.id,
        "pass_number": harvest.pass_number,
        "payment_type": work.payment_type,
        "kg_collected": work.kg_collected,
    }


def labor_item(labor: DayLabor) -> dict:
    return {
        "kind": "day_labor",
        "id": labor.id,
        "farm_id": labor.employee.farm_id,
        "employee_id": labor.employee_id,
        "employee_name": labor.employee.full_name,
        "item_date": labor.labor_date,
        "amount": labor.daily_value,
        "paid": labor.paid,
        "paid_at": labor.paid_at,
        "plot_name": labor.plot.name if labor.plot else None,
        "activity_type": labor.activity_type,
        "other_detail": labor.other_detail,
    }
