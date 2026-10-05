from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dashboard.schema import (
    AlertResponse,
    CycleState,
    DashboardSummary,
    FarmRanking,
    ProductionCharts,
    QualityCharts,
    SeasonResponse,
)
from app.farm_operations.api.v1.dashboard.service import DashboardService
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.quality_projection.schema import QualityProjectionResponse
from app.farm_operations.api.v1.quality_projection.service import ProjectionService
from app.farm_operations.services.access import FarmAccess

router = APIRouter()

FARM = Query(None, description="Una finca; vacío = todas las del alcance")
FROM = Query(None, description="Inicio del periodo (por defecto, hace 12 meses)")
TO = Query(None, description="Fin del periodo (por defecto, hoy)")


def get_service(
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
) -> DashboardService:
    return DashboardService(db, access)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    farm_id: Optional[int] = FARM,
    date_from: Optional[date] = FROM,
    date_to: Optional[date] = TO,
    service: DashboardService = Depends(get_service),
):
    """KPIs: los de estado muestran el ahora; los de periodo, el rango."""
    return service.summary(farm_id, date_from, date_to)


@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(farm_id: Optional[int] = FARM, service: DashboardService = Depends(get_service)):
    """Alertas y recordatorios activos, de la más grave y antigua a la más leve."""
    return service.alerts(farm_id)


@router.get("/production", response_model=ProductionCharts)
def get_production(
    farm_id: Optional[int] = FARM,
    date_from: Optional[date] = FROM,
    date_to: Optional[date] = TO,
    service: DashboardService = Depends(get_service),
):
    return service.production(farm_id, date_from, date_to)


@router.get("/quality", response_model=QualityCharts)
def get_quality(
    farm_id: Optional[int] = FARM,
    date_from: Optional[date] = FROM,
    date_to: Optional[date] = TO,
    service: DashboardService = Depends(get_service),
):
    return service.quality(farm_id, date_from, date_to)


@router.get("/periods", response_model=List[SeasonResponse])
def get_periods(
    farm_id: Optional[int] = FARM,
    plot_id: Optional[int] = Query(None),
    service: DashboardService = Depends(get_service),
):
    """Temporadas de cosecha, la más reciente primero (botones «Última(s) N cosecha(s)»)."""
    return service.periods(farm_id, plot_id)


@router.get("/cycles", response_model=List[CycleState])
def get_cycles(farm_id: Optional[int] = FARM, service: DashboardService = Depends(get_service)):
    """Estado de los ciclos activos: última labor, cosecha estimada y alertas."""
    return service.cycles(farm_id)


@router.get("/farms", response_model=List[FarmRanking])
def get_farms(
    date_from: Optional[date] = FROM,
    date_to: Optional[date] = TO,
    service: DashboardService = Depends(get_service),
):
    """Ranking de fincas: producción, rendimiento, puntaje, alertas y sanidad."""
    return service.farms(date_from, date_to)


@router.get("/quality-projections", response_model=List[QualityProjectionResponse])
def get_quality_projections(
    farm_id: Optional[int] = FARM,
    db: Session = Depends(get_db),
    access: FarmAccess = Depends(get_farm_access),
):
    """Proyección de calidad de los ciclos activos del alcance, por finca y lote."""
    return ProjectionService(db, access).for_farms(farm_id)
