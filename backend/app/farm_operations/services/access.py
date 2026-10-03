from typing import Optional

from sqlalchemy.orm import Query, Session

from app.core.exceptions.domain import DomainError, NotFoundError, PermissionDeniedError
from app.core.roles import UserRole
from app.farm_operations.models import CropCycle, DayLabor, Employee, Farm, Harvest, HarvestWork, Plot
from app.models.farmer import Farmer


class FarmAccess:
    """
    Alcance de un usuario sobre las fincas y todo lo que cuelga de ellas.

    - `admin`: todas las fincas.
    - `farmer`: solo las fincas de su registro de caficultor, que comparte
      su persona con la cuenta de usuario.

    Un recurso fuera del alcance responde 404, igual que uno inexistente,
    para no revelar qué existe (especificacion-api §2).
    """

    def __init__(self, db: Session, user):
        self.db = db
        self.is_admin = user.role == UserRole.admin.value
        self.farmer_id: Optional[int] = None

        if not self.is_admin:
            farmer = (
                db.query(Farmer.id)
                .filter(Farmer.person_id == user.person_id)
                .first()
            )
            self.farmer_id = farmer.id if farmer else None

    # ── Fincas ────────────────────────────────────────────────────────────

    def farms(self) -> Query:
        """Fincas visibles para el usuario."""
        query = self.db.query(Farm)
        if not self.is_admin:
            # Sin registro de caficultor, el filtro no devuelve nada
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_farm(self, farm_id: int) -> Farm:
        farm = self.farms().filter(Farm.id == farm_id).first()
        if not farm:
            raise NotFoundError("Finca no encontrada")
        return farm

    def owner_for_new_farm(self, farmer_id: Optional[int]) -> int:
        """
        Caficultor dueño de una finca nueva.

        El administrador indica cualquier caficultor; un caficultor registra
        siempre a su propio nombre.
        """
        if self.is_admin:
            if farmer_id is None:
                raise DomainError("Indica el caficultor dueño de la finca")
            if not self.db.query(Farmer.id).filter(Farmer.id == farmer_id).first():
                raise NotFoundError("Caficultor no encontrado")
            return farmer_id

        if self.farmer_id is None:
            raise PermissionDeniedError("Tu cuenta no está asociada a un caficultor")
        if farmer_id is not None and farmer_id != self.farmer_id:
            raise PermissionDeniedError("Solo puedes registrar fincas a tu nombre")
        return self.farmer_id

    # ── Lotes ─────────────────────────────────────────────────────────────

    def plots(self) -> Query:
        """Lotes de las fincas visibles para el usuario."""
        query = self.db.query(Plot).join(Plot.farm)
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_plot(self, plot_id: int) -> Plot:
        plot = self.plots().filter(Plot.id == plot_id).first()
        if not plot:
            raise NotFoundError("Lote no encontrado")
        return plot

    # ── Ciclos y registros ────────────────────────────────────────────────

    def cycles(self) -> Query:
        """Ciclos de los lotes visibles para el usuario."""
        query = self.db.query(CropCycle).join(CropCycle.plot).join(Plot.farm)
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_cycle(self, cycle_id: int) -> CropCycle:
        cycle = self.cycles().filter(CropCycle.id == cycle_id).first()
        if not cycle:
            raise NotFoundError("Ciclo no encontrado")
        return cycle

    def cycle_records(self, model) -> Query:
        """Registros de `model` que cuelgan de un ciclo visible (labores)."""
        query = (
            self.db.query(model)
            .join(CropCycle, model.crop_cycle_id == CropCycle.id)
            .join(Plot, CropCycle.plot_id == Plot.id)
            .join(Farm, Plot.farm_id == Farm.id)
        )
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_harvest(self, harvest_id: int) -> Harvest:
        harvest = self.cycle_records(Harvest).filter(Harvest.id == harvest_id).first()
        if not harvest:
            raise NotFoundError("Cosecha no encontrada")
        return harvest

    def harvest_works(self) -> Query:
        """Recolección de las cosechas visibles para el usuario."""
        query = (
            self.db.query(HarvestWork)
            .join(Harvest, HarvestWork.harvest_id == Harvest.id)
            .join(CropCycle, Harvest.crop_cycle_id == CropCycle.id)
            .join(Plot, CropCycle.plot_id == Plot.id)
            .join(Farm, Plot.farm_id == Farm.id)
        )
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_harvest_work(self, work_id: int) -> HarvestWork:
        work = self.harvest_works().filter(HarvestWork.id == work_id).first()
        if not work:
            raise NotFoundError("Registro de recolección no encontrado")
        return work

    def day_labors(self) -> Query:
        """Jornales de los empleados de las fincas visibles para el usuario."""
        query = (
            self.db.query(DayLabor)
            .join(Employee, DayLabor.employee_id == Employee.id)
            .join(Farm, Employee.farm_id == Farm.id)
        )
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_day_labor(self, labor_id: int) -> DayLabor:
        labor = self.day_labors().filter(DayLabor.id == labor_id).first()
        if not labor:
            raise NotFoundError("Jornal no encontrado")
        return labor

    def plot_records(self, model) -> Query:
        """Registros de `model` que cuelgan de un lote visible (análisis de suelo)."""
        query = self.db.query(model).join(Plot, model.plot_id == Plot.id).join(Farm, Plot.farm_id == Farm.id)
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def farm_records(self, model) -> Query:
        """Registros de `model` que cuelgan de una finca visible (clima)."""
        query = self.db.query(model).join(Farm, model.farm_id == Farm.id)
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    # ── Empleados ─────────────────────────────────────────────────────────

    def employees(self) -> Query:
        """Empleados de las fincas visibles para el usuario."""
        query = self.db.query(Employee).join(Employee.farm)
        if not self.is_admin:
            query = query.filter(Farm.farmer_id == self.farmer_id)
        return query

    def get_employee(self, employee_id: int) -> Employee:
        employee = self.employees().filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundError("Empleado no encontrado")
        return employee
