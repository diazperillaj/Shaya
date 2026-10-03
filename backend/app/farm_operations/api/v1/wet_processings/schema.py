from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import moment_not_in_future, require_other_detail
from app.farm_operations.models.enums import (
    FermentationMethodEnum,
    HarvestStatusEnum,
    WetProcessingStatusEnum,
)

KG = {"max_digits": 10, "decimal_places": 3}


class WetInputItem(BaseModel):
    harvest_id: int = Field(..., gt=0)
    cherry_kg: Decimal = Field(..., gt=0, description="Café cereza que aporta la cosecha", **KG)


def unique_harvests(items: List[WetInputItem]) -> List[WetInputItem]:
    ids = [item.harvest_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Cada cosecha va una sola vez")
    return items


class WetProcessingStages(BaseModel):
    """Etapas del beneficio; se registran a medida que ocurren."""

    # 1. Selección de flotes
    floats_kg: Optional[Decimal] = Field(None, ge=0, **KG)
    floats_method: Optional[str] = Field(None, max_length=100, description="Tanque, zaranda…")
    # 2. Despulpado
    pulped_at: Optional[datetime] = None
    # 3. Fermentación
    fermentation_start: Optional[datetime] = None
    fermentation_end: Optional[datetime] = None
    fermentation_method: Optional[FermentationMethodEnum] = None
    fermentation_other_detail: Optional[str] = Field(None, max_length=150)
    fermentation_decided_by: Optional[str] = Field(None, max_length=150, description="Quién indicó el punto de lavado")
    fermentation_criteria: Optional[str] = Field(None, max_length=255, description="Prueba de tacto, palote, pH…")
    ambient_temp_c: Optional[Decimal] = Field(None, ge=-10, le=50, max_digits=4, decimal_places=1)
    # 4. Lavado
    wash_count: Optional[int] = Field(None, ge=1)
    washed_kg: Optional[Decimal] = Field(None, gt=0, description="Café lavado que sale a secado", **KG)
    observations: Optional[str] = None

    @field_validator("pulped_at", "fermentation_start", "fermentation_end")
    @classmethod
    def moments_not_in_future(cls, value):
        return moment_not_in_future(value, "La fecha")

    @model_validator(mode="after")
    def consistent_fermentation(self):
        if self.fermentation_end is not None:
            if self.fermentation_start is None:
                raise ValueError("Indica cuándo empezó la fermentación")
            if self.fermentation_end < self.fermentation_start:
                raise ValueError("La fermentación no puede terminar antes de empezar")
        require_other_detail(
            self.fermentation_method == FermentationMethodEnum.other,
            self.fermentation_other_detail,
            "Indica cuál método de fermentación",
        )
        return self


class WetProcessingCreate(WetProcessingStages):
    farm_id: int = Field(..., gt=0)
    inputs: List[WetInputItem] = Field(..., min_length=1)

    @field_validator("inputs")
    @classmethod
    def one_per_harvest(cls, value):
        return unique_harvests(value)


class WetProcessingUpdate(WetProcessingStages):
    pass


class WetInputsReplace(BaseModel):
    inputs: List[WetInputItem] = Field(..., min_length=1)

    @field_validator("inputs")
    @classmethod
    def one_per_harvest(cls, value):
        return unique_harvests(value)


class WetCompleteRequest(BaseModel):
    washed_kg: Optional[Decimal] = Field(None, gt=0, description="Vacío = el ya registrado", **KG)


class WetInputResponse(BaseModel):
    harvest_id: int
    cherry_kg: Decimal
    plot_id: int
    plot_name: str
    cycle_number: int
    pass_number: int
    harvest_status: HarvestStatusEnum


class WetProcessingResponse(BaseModel):
    id: int
    farm_id: int
    farm_name: str
    status: WetProcessingStatusEnum
    floats_kg: Optional[Decimal]
    floats_method: Optional[str]
    pulped_at: Optional[datetime]
    fermentation_start: Optional[datetime]
    fermentation_end: Optional[datetime]
    fermentation_method: Optional[FermentationMethodEnum]
    fermentation_other_detail: Optional[str]
    fermentation_decided_by: Optional[str]
    fermentation_criteria: Optional[str]
    ambient_temp_c: Optional[Decimal]
    wash_count: Optional[int]
    washed_kg: Optional[Decimal]
    observations: Optional[str]
    created_at: datetime
    cherry_kg: Decimal = Field(..., description="Café cereza que entró (suma de los aportes)")
    fermentation_hours: Optional[Decimal] = Field(None, description="Calculadas entre inicio y fin")
    washed_kg_dried: Decimal = Field(..., description="Café lavado ya repartido en secados")
    inputs: List[WetInputResponse]
