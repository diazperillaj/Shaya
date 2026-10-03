from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions.domain import NotFoundError
from app.farm_operations.api.v1.dryings.service import DryingService
from app.farm_operations.models import CropCycle
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.cycle_records import records_summary
from app.farm_operations.services.mass_balance import cherry_in, harvest_processed_kg
from app.farm_operations.services.traceability import drying_composition, harvest_destinations
from app.models.parchment import Parchment

ZERO = Decimal(0)


class TraceabilityService:
    """
    Recorre la cadena en ambos sentidos (modelo-datos §7): de un secado (o
    del pergamino que produjo) hacia sus lotes, ciclos y labores, y de una
    cosecha hacia los beneficios, secados y pergaminos que recibieron su café.
    """

    def __init__(self, db: Session, access: FarmAccess):
        self.db = db
        self.access = access

    def drying(self, drying_id: int) -> dict:
        drying = self.access.get_drying(drying_id)
        composition = drying_composition(drying)["composition"]

        cycle_ids = {harvest["crop_cycle_id"] for plot in composition for harvest in plot["harvests"]}
        cycles = {cycle.id: cycle for cycle in self.db.query(CropCycle).filter(CropCycle.id.in_(cycle_ids))}

        plots = []
        for plot in composition:
            by_cycle = defaultdict(list)
            for harvest in plot["harvests"]:
                by_cycle[harvest["crop_cycle_id"]].append(harvest)
            plots.append({
                **{key: plot[key] for key in ("plot_id", "plot_name", "variety", "cherry_kg", "share_pct")},
                "cycles": [
                    {
                        "crop_cycle_id": cycle_id,
                        "cycle_number": cycles[cycle_id].cycle_number,
                        "start_date": cycles[cycle_id].start_date,
                        "end_date": cycles[cycle_id].end_date,
                        "status": cycles[cycle_id].status,
                        "cherry_kg": sum((h["cherry_kg"] for h in harvests), ZERO),
                        "harvests": harvests,
                        "labors": records_summary(self.db, cycle_id),
                    }
                    for cycle_id, harvests in sorted(by_cycle.items(), key=lambda item: cycles[item[0]].cycle_number)
                ],
            })

        return {
            "drying": DryingService(self.db, self.access).get_one(drying.id),
            "plots": plots,
            "wet_processings": [
                {
                    "wet_processing_id": item.wet_processing_id,
                    "pulped_at": item.wet_processing.pulped_at,
                    "cherry_kg": cherry_in(item.wet_processing),
                    "washed_kg": item.wet_processing.washed_kg,
                    "wet_kg": item.wet_kg,
                }
                for item in drying.inputs
            ],
        }

    def parchment(self, parchment_id: int) -> dict:
        """La trazabilidad del secado que produjo un pergamino del inventario."""
        parchment = self.db.get(Parchment, parchment_id)
        if parchment is None:
            raise NotFoundError("Pergamino no encontrado")
        if parchment.drying_id is None:
            raise NotFoundError("Este pergamino es comprado: no tiene trazabilidad de cultivo")
        return self.drying(parchment.drying_id)

    def harvest(self, harvest_id: int) -> dict:
        harvest = self.access.get_harvest(harvest_id)
        cycle = harvest.crop_cycle
        return {
            "harvest_id": harvest.id,
            "pass_number": harvest.pass_number,
            "plot_id": cycle.plot_id,
            "plot_name": cycle.plot.name,
            "cycle_number": cycle.cycle_number,
            "status": harvest.status,
            "total_cherry_kg": harvest.total_cherry_kg,
            "processed_kg": harvest_processed_kg(self.db, harvest.id),
            "destinations": harvest_destinations(self.db, harvest),
        }
