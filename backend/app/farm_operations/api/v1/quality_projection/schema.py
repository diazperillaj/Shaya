"""Contrato de la proyección de calidad (especificacion-api §3.14)."""

from datetime import date
from typing import List, Literal

from pydantic import BaseModel, Field

Stage = Literal["pre", "harvest", "wet", "drying"]


class QualityProjectionResponse(BaseModel):
    crop_cycle_id: int
    cycle_number: int
    plot_id: int
    plot_name: str
    farm_id: int
    farm_name: str
    as_of: date
    score: float = Field(description="Puntaje SCA esperado")
    defects_pct: float
    yield_factor: float = Field(description="kg de pergamino seco por 70 kg de excelso (menor es mejor)")
    completeness: float = Field(description="Fracción de grupos de features con al menos un dato (0–1)")
    stages: List[Stage] = Field(description="Etapas que ya ocurrieron; las demás se rellenan con la finca")
    model_version: str
    disclaimer: str
