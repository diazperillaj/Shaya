from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.api.v1.farms.schema import FarmCreate, FarmUpdate
from app.farm_operations.models import Employee, Farm, Plot
from app.farm_operations.models.enums import PlotStatusEnum
from app.farm_operations.services.access import FarmAccess


class FarmService:
    """Fincas del módulo de cultivo, siempre dentro del alcance del usuario."""

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def get_farms(self, search: Optional[str] = None, active: Optional[bool] = None) -> List[dict]:
        query = self.access.farms()
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Farm.name.ilike(pattern),
                    Farm.village.ilike(pattern),
                    Farm.municipality.ilike(pattern),
                )
            )
        if active is not None:
            query = query.filter(Farm.active == active)

        farms = query.order_by(Farm.name).all()
        counts = self._active_plots([farm.id for farm in farms])
        return [self._to_response(farm, counts.get(farm.id, 0)) for farm in farms]

    def get_farm(self, farm_id: int) -> dict:
        farm = self.access.get_farm(farm_id)
        return self._to_response(farm, self._active_plots([farm.id]).get(farm.id, 0))

    def create_farm(self, payload: FarmCreate) -> dict:
        farmer_id = self.access.owner_for_new_farm(payload.farmer_id)
        self._validate_unique_name(farmer_id, payload.name)

        farm = Farm(farmer_id=farmer_id, **self._fields(payload))
        self.db.add(farm)
        self.db.commit()
        return self.get_farm(farm.id)

    def update_farm(self, farm_id: int, payload: FarmUpdate) -> dict:
        farm = self.access.get_farm(farm_id)
        self._validate_unique_name(farm.farmer_id, payload.name, exclude_id=farm.id)

        for field, value in self._fields(payload).items():
            setattr(farm, field, value)
        farm.active = payload.active
        self.db.commit()
        return self.get_farm(farm.id)

    def delete_farm(self, farm_id: int) -> None:
        farm = self.access.get_farm(farm_id)

        if self.db.query(Plot.id).filter(Plot.farm_id == farm.id).first():
            raise ConflictError("No se puede eliminar: la finca tiene lotes registrados")
        if self.db.query(Employee.id).filter(Employee.farm_id == farm.id).first():
            raise ConflictError("No se puede eliminar: la finca tiene empleados registrados")

        self.db.delete(farm)
        self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    @staticmethod
    def _fields(payload) -> dict:
        return {
            "name": payload.name.strip(),
            "village": payload.village.strip(),
            "municipality": payload.municipality.strip(),
            "altitude": payload.altitude,
            "total_area": payload.total_area,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "observations": payload.observations,
        }

    def _validate_unique_name(self, farmer_id: int, name: str, exclude_id: Optional[int] = None) -> None:
        query = self.db.query(Farm.id).filter(
            Farm.farmer_id == farmer_id, Farm.name.ilike(name.strip())
        )
        if exclude_id is not None:
            query = query.filter(Farm.id != exclude_id)
        if query.first():
            raise ConflictError(f"Ya existe una finca llamada «{name.strip()}» para este caficultor")

    def _active_plots(self, farm_ids: List[int]) -> dict:
        """Cantidad de lotes activos por finca."""
        if not farm_ids:
            return {}
        rows = (
            self.db.query(Plot.farm_id, func.count(Plot.id))
            .filter(Plot.farm_id.in_(farm_ids), Plot.status == PlotStatusEnum.active)
            .group_by(Plot.farm_id)
            .all()
        )
        return dict(rows)

    @staticmethod
    def _to_response(farm: Farm, active_plots: int) -> dict:
        return {
            "id": farm.id,
            "farmer": {"id": farm.farmer.id, "full_name": farm.farmer.person.full_name},
            "name": farm.name,
            "village": farm.village,
            "municipality": farm.municipality,
            "altitude": farm.altitude,
            "total_area": farm.total_area,
            "latitude": farm.latitude,
            "longitude": farm.longitude,
            "active": farm.active,
            "observations": farm.observations,
            "created_at": farm.created_at,
            "active_plots": active_plots,
        }
