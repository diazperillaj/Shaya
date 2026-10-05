from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.ml.predictor import project_cycles
from app.farm_operations.models import CropCycle, Farm, Plot
from app.farm_operations.models.enums import CycleStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.dates import business_today


class ProjectionService:
    """Proyección de calidad del ciclo activo de un lote, o de todos los del alcance."""

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def for_plot(self, plot_id: int) -> dict:
        plot = self.access.get_plot(plot_id)
        cycle = (
            self.db.query(CropCycle.id)
            .filter(CropCycle.plot_id == plot.id, CropCycle.status == CycleStatusEnum.active)
            .first()
        )
        if cycle is None:
            raise ConflictError("El lote no tiene un ciclo activo: la proyección es del ciclo en curso")
        [projection] = project_cycles(self.db, [cycle.id], business_today())
        return projection.as_dict()

    def for_farms(self, farm_id: Optional[int]) -> list[dict]:
        """Los ciclos activos de una finca o de todas las del alcance, por finca y lote."""
        if farm_id is not None:
            farm_ids = [self.access.get_farm(farm_id).id]
        else:
            farm_ids = [row[0] for row in self.access.farms().with_entities(Farm.id).all()]
        cycle_ids = [
            row[0] for row in (
                self.db.query(CropCycle.id).join(Plot, CropCycle.plot_id == Plot.id)
                .filter(Plot.farm_id.in_(farm_ids), CropCycle.status == CycleStatusEnum.active)
            )
        ]
        projections = project_cycles(self.db, cycle_ids, business_today())
        return [p.as_dict() for p in sorted(projections, key=lambda p: (p.farm_name, p.plot_name, p.plot_id))]
