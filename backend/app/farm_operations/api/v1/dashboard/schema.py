"""
Contratos del dashboard de cultivo (dashboards-alertas §2–§5).

Son de solo lectura y de presentación: los agregados viajan como números
(float), y las gráficas reutilizan el contrato `BarChartData` del dashboard
existente, para que el frontend use los mismos componentes.
"""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.api.api_v1.dashboard.schema import BarChartData

Unit = Literal["farm", "plot"]


class Period(BaseModel):
    date_from: date
    date_to: date


class VarietyArea(BaseModel):
    variety: str
    area_ha: float


class InProcess(BaseModel):
    count: int
    kg: float = Field(..., description="Cereza en beneficio o café lavado en secado")
    oldest_days: Optional[int] = Field(None, description="Días del más antiguo")


class StoredDrying(BaseModel):
    drying_id: int
    farm_id: int
    farm_name: str
    end_date: date
    output_kg: float
    days: int


class DashboardSummary(BaseModel):
    period: Period
    # Estado: siempre el ahora
    farms_active: int
    plots_active: int
    area_by_variety: List[VarietyArea]
    cycles_active: int
    harvests_open: int
    wet_in_progress: InProcess
    drying_in_progress: InProcess
    stored_parchment_kg: float
    pending_payments: float
    stored_dryings: List[StoredDrying] = Field(..., description="Café guardado en finca, del más antiguo al más nuevo")
    # Periodo
    cherry_kg: float = Field(..., description="Cereza de las cosechas cerradas en el periodo")
    parchment_kg: float = Field(..., description="Pergamino seco de los secados cerrados en el periodo")
    yield_pct: Optional[float] = Field(None, description="Pergamino seco / cereza trazada (F2)")
    yield_history_pct: Optional[float] = Field(None, description="El mismo rendimiento en los 12 meses previos")
    harvest_cost: float = Field(..., description="Recolección de las cosechas cerradas en el periodo")
    score_avg: Optional[float] = None
    evaluations: int


class AlertResponse(BaseModel):
    type: str
    severity: Literal["info", "medium", "high"]
    farm_id: int
    farm_name: str
    plot_id: Optional[int]
    plot_name: Optional[str]
    entity: dict
    message: str
    value: Optional[float]
    threshold: Optional[float]
    since: Optional[date]


class ProductionCharts(BaseModel):
    unit: Unit = Field(..., description="Las gráficas por unidad van por lote (una finca) o por finca")
    monthly: BarChartData
    by_unit: BarChartData
    yield_by_unit: BarChartData
    yield_reference_pct: Optional[float] = Field(None, description="Rendimiento del alcance en los 12 meses previos")
    by_variety: BarChartData
    picking_cost: BarChartData
    pipeline: BarChartData


class QualityCharts(BaseModel):
    unit: Unit
    score_distribution: BarChartData
    score_by_variety: BarChartData
    score_defects_by_unit: BarChartData
    score_evolution: BarChartData
    broca_by_unit: BarChartData
    roya_by_unit: BarChartData
    humidity_distribution: BarChartData
    humidity_range: tuple[Optional[float], Optional[float]]


class SeasonResponse(BaseModel):
    label: str
    date_from: date
    date_to: date
    harvests: int
    cherry_kg: float
    open: bool


class LastLabor(BaseModel):
    kind: str
    date: date


class CycleState(BaseModel):
    crop_cycle_id: int
    cycle_number: int
    plot_id: int
    plot_name: str
    farm_id: int
    farm_name: str
    start_date: date
    days: int
    last_labor: Optional[LastLabor]
    harvest_status: Literal["waiting", "open", "harvested"]
    estimated_harvest: Optional[date] = Field(None, description="Floración principal + 224 días (±14)")
    alerts: int


class FarmRanking(BaseModel):
    farm_id: int
    farm_name: str
    plots_active: int
    cherry_kg: float
    parchment_kg: float
    yield_pct: Optional[float]
    score_avg: Optional[float]
    alerts_high: int
    alerts_medium: int
    alerts_info: int
    broca_pct: Optional[float] = Field(None, description="El mayor de los últimos muestreos de sus lotes")
    roya_pct: Optional[float]
    broca_threshold: Optional[float]
    stored_kg: float
