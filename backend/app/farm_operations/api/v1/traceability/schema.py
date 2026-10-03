from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.farm_operations.api.v1.crop_cycles.schema import RecordSummary
from app.farm_operations.api.v1.dryings.schema import DryingResponse
from app.farm_operations.models.enums import (
    CycleStatusEnum,
    DryingDestinationEnum,
    DryingStatusEnum,
    HarvestStatusEnum,
    WetProcessingStatusEnum,
)


class TraceHarvest(BaseModel):
    harvest_id: int
    pass_number: int
    cherry_kg: Decimal


class TraceCycle(BaseModel):
    crop_cycle_id: int
    cycle_number: int
    start_date: date
    end_date: Optional[date]
    status: CycleStatusEnum
    cherry_kg: Decimal
    harvests: List[TraceHarvest]
    labors: List[RecordSummary]


class TracePlot(BaseModel):
    plot_id: int
    plot_name: str
    variety: str
    cherry_kg: Decimal
    share_pct: Decimal
    cycles: List[TraceCycle]


class TraceWetProcessing(BaseModel):
    wet_processing_id: int
    pulped_at: Optional[datetime]
    cherry_kg: Decimal
    washed_kg: Optional[Decimal]
    wet_kg: Decimal


class DryingTrace(BaseModel):
    """Hacia atrás: de un secado a sus lotes, ciclos, cosechas y labores."""

    drying: DryingResponse
    plots: List[TracePlot]
    wet_processings: List[TraceWetProcessing]


class DestinationDrying(BaseModel):
    drying_id: int
    status: DryingStatusEnum
    destination: Optional[DryingDestinationEnum]
    cherry_kg: Decimal
    parchment_id: Optional[int]


class Destination(BaseModel):
    wet_processing_id: int
    status: WetProcessingStatusEnum
    cherry_kg: Decimal
    dryings: List[DestinationDrying]


class HarvestTrace(BaseModel):
    """Hacia adelante: a qué beneficios, secados y pergaminos fue el café de una cosecha."""

    harvest_id: int
    pass_number: int
    plot_id: int
    plot_name: str
    cycle_number: int
    status: HarvestStatusEnum
    total_cherry_kg: Optional[Decimal]
    processed_kg: Decimal
    destinations: List[Destination]
