"""
Esquemas de las labores del ciclo.

Cada labor separa sus campos en dos grupos, para registrarla en uno o en
varios lotes con los mismos esquemas:

- *Shared*: lo que es igual en todos los lotes (fecha, insumo, método…).
- *Amounts*: lo que es de cada lote (cantidad, costo, volumen), que en el
  registro múltiple se reparte por área.

`Create` y `Update` llevan ambos grupos; `Bulk` lleva los campos comunes y
una lista de `items` con el ciclo y los montos de cada lote.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future, require_other_detail
from app.farm_operations.models.enums import (
    CulturalPracticeTypeEnum,
    FertilizationMethodEnum,
    IntensityEnum,
    SeverityEnum,
)

Cost = Optional[Decimal]
PERCENT = {"ge": 0, "le": 100, "max_digits": 5, "decimal_places": 2}


def cost_field():
    return Field(None, ge=0, max_digits=12, decimal_places=2, description="Pesos colombianos")


class CycleItem(BaseModel):
    crop_cycle_id: int = Field(..., gt=0)


class BulkItems(BaseModel):
    """Validación común del registro en varios lotes."""

    @model_validator(mode="after")
    def one_item_per_cycle(self):
        ids = [item.crop_cycle_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada lote va una sola vez")
        return self


class SupplyRef(BaseModel):
    id: int
    name: str
    unit: str


class LaborResponse(BaseModel):
    id: int
    crop_cycle_id: int
    cycle_number: int
    plot_id: int
    plot_name: str
    observations: Optional[str]
    created_at: datetime


# ── Fertilizaciones ───────────────────────────────────────────────────────


class FertilizationShared(BaseModel):
    supply_id: int = Field(..., gt=0)
    application_date: date
    method: FertilizationMethodEnum
    dose_per_tree_g: Optional[Decimal] = Field(None, gt=0, max_digits=8, decimal_places=2)
    observations: Optional[str] = None

    @field_validator("application_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de aplicación")


class FertilizationAmounts(BaseModel):
    quantity: Decimal = Field(
        ..., gt=0, max_digits=10, decimal_places=3,
        description="Total aplicado al lote, en la unidad del insumo",
    )
    cost: Cost = cost_field()


class FertilizationUpdate(FertilizationShared, FertilizationAmounts):
    pass


class FertilizationCreate(FertilizationUpdate, CycleItem):
    pass


class FertilizationItem(FertilizationAmounts, CycleItem):
    pass


class FertilizationBulk(FertilizationShared, BulkItems):
    items: List[FertilizationItem] = Field(..., min_length=1)


class FertilizationResponse(LaborResponse):
    supply_id: int
    supply: SupplyRef
    application_date: date
    method: FertilizationMethodEnum
    quantity: Decimal
    dose_per_tree_g: Optional[Decimal]
    cost: Optional[Decimal]


# ── Aplicaciones fitosanitarias ───────────────────────────────────────────


class PhytosanitaryShared(BaseModel):
    supply_id: int = Field(..., gt=0)
    application_date: date
    target: str = Field(..., min_length=1, max_length=100, description="Broca, roya, maleza…")
    dose_description: Optional[str] = Field(None, max_length=255, description="«20 cc por bomba de 20 L»")
    observations: Optional[str] = None

    @field_validator("application_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de aplicación")


class PhytosanitaryAmounts(BaseModel):
    quantity: Decimal = Field(
        ..., gt=0, max_digits=10, decimal_places=3,
        description="Total aplicado al lote, en la unidad del insumo",
    )
    cost: Cost = cost_field()


class PhytosanitaryUpdate(PhytosanitaryShared, PhytosanitaryAmounts):
    pass


class PhytosanitaryCreate(PhytosanitaryUpdate, CycleItem):
    pass


class PhytosanitaryItem(PhytosanitaryAmounts, CycleItem):
    pass


class PhytosanitaryBulk(PhytosanitaryShared, BulkItems):
    items: List[PhytosanitaryItem] = Field(..., min_length=1)


class PhytosanitaryResponse(LaborResponse):
    supply_id: int
    supply: SupplyRef
    application_date: date
    target: str
    quantity: Decimal
    dose_description: Optional[str]
    cost: Optional[Decimal]


# ── Riegos ────────────────────────────────────────────────────────────────


class IrrigationShared(BaseModel):
    irrigation_date: date
    method: Optional[str] = Field(None, max_length=100, description="Aspersión, goteo, manguera…")
    duration_minutes: Optional[int] = Field(None, gt=0)
    observations: Optional[str] = None

    @field_validator("irrigation_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha del riego")


class IrrigationAmounts(BaseModel):
    volume_liters: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=1)


class IrrigationUpdate(IrrigationShared, IrrigationAmounts):
    pass


class IrrigationCreate(IrrigationUpdate, CycleItem):
    pass


class IrrigationItem(IrrigationAmounts, CycleItem):
    pass


class IrrigationBulk(IrrigationShared, BulkItems):
    items: List[IrrigationItem] = Field(..., min_length=1)


class IrrigationResponse(LaborResponse):
    irrigation_date: date
    method: Optional[str]
    duration_minutes: Optional[int]
    volume_liters: Optional[Decimal]


# ── Monitoreos de plagas (propios de cada lote: sin registro múltiple) ─────


class PestMonitoringUpdate(BaseModel):
    monitoring_date: date
    broca_pct: Optional[Decimal] = Field(None, **PERCENT)
    roya_pct: Optional[Decimal] = Field(None, **PERCENT)
    other_pest: Optional[str] = Field(None, max_length=100, description="Cochinilla, minador…")
    other_pest_pct: Optional[Decimal] = Field(None, **PERCENT)
    severity: Optional[SeverityEnum] = None
    observations: Optional[str] = None

    @field_validator("monitoring_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha del monitoreo")

    @model_validator(mode="after")
    def has_a_result(self):
        other = (self.other_pest or "").strip()
        if self.broca_pct is None and self.roya_pct is None and not other:
            raise ValueError("Registra al menos un resultado: broca, roya u otra plaga")
        if self.other_pest_pct is not None and not other:
            raise ValueError("Indica cuál es la otra plaga")
        return self


class PestMonitoringCreate(PestMonitoringUpdate, CycleItem):
    pass


class PestMonitoringResponse(LaborResponse):
    monitoring_date: date
    broca_pct: Optional[Decimal]
    roya_pct: Optional[Decimal]
    other_pest: Optional[str]
    other_pest_pct: Optional[Decimal]
    severity: Optional[SeverityEnum]


# ── Labores culturales ────────────────────────────────────────────────────


class CulturalPracticeShared(BaseModel):
    practice_type: CulturalPracticeTypeEnum
    other_detail: Optional[str] = Field(None, max_length=150, description="Cuál labor, cuando es `other`")
    practice_date: date
    observations: Optional[str] = None

    @field_validator("practice_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de la labor")

    @model_validator(mode="after")
    def other_needs_detail(self):
        require_other_detail(
            self.practice_type == CulturalPracticeTypeEnum.other, self.other_detail, "Indica cuál labor es"
        )
        return self


class CulturalPracticeAmounts(BaseModel):
    cost: Cost = cost_field()


class CulturalPracticeUpdate(CulturalPracticeShared, CulturalPracticeAmounts):
    pass


class CulturalPracticeCreate(CulturalPracticeUpdate, CycleItem):
    pass


class CulturalPracticeItem(CulturalPracticeAmounts, CycleItem):
    pass


class CulturalPracticeBulk(CulturalPracticeShared, BulkItems):
    items: List[CulturalPracticeItem] = Field(..., min_length=1)


class CulturalPracticeResponse(LaborResponse):
    practice_type: CulturalPracticeTypeEnum
    other_detail: Optional[str]
    practice_date: date
    cost: Optional[Decimal]


# ── Floraciones ───────────────────────────────────────────────────────────


class FloweringShared(BaseModel):
    flowering_date: date
    intensity: IntensityEnum
    observations: Optional[str] = None

    @field_validator("flowering_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de floración")


class FloweringUpdate(FloweringShared):
    pass


class FloweringCreate(FloweringUpdate, CycleItem):
    pass


class FloweringBulk(FloweringShared, BulkItems):
    items: List[CycleItem] = Field(..., min_length=1)


class FloweringResponse(LaborResponse):
    flowering_date: date
    intensity: IntensityEnum
