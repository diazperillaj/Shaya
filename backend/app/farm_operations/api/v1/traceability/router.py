from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.traceability.schema import DryingTrace, HarvestTrace
from app.farm_operations.api.v1.traceability.service import TraceabilityService
from app.farm_operations.services.access import FarmAccess

router = APIRouter()


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> TraceabilityService:
    return TraceabilityService(db, access)


@router.get("/dryings/{drying_id}", response_model=DryingTrace)
def drying_trace(drying_id: int, service: TraceabilityService = Depends(get_service)):
    """De un secado a sus lotes, ciclos, cosechas y labores, con la participación de cada lote."""
    return service.drying(drying_id)


@router.get("/parchments/{parchment_id}", response_model=DryingTrace)
def parchment_trace(parchment_id: int, service: TraceabilityService = Depends(get_service)):
    """De un pergamino del inventario al secado que lo produjo y, de ahí, a sus lotes."""
    return service.parchment(parchment_id)


@router.get("/harvests/{harvest_id}", response_model=HarvestTrace)
def harvest_trace(harvest_id: int, service: TraceabilityService = Depends(get_service)):
    """De una cosecha a los beneficios, secados y pergaminos que recibieron su café."""
    return service.harvest(harvest_id)
