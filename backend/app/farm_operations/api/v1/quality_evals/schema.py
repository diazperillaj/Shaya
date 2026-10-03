from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.farm_operations.api.v1.validation import not_in_future
from app.farm_operations.models.enums import QualityStageEnum
from app.farm_operations.services.dates import business_today

PERCENT = {"ge": 0, "le": 100, "max_digits": 5, "decimal_places": 2}

# Resultados de cada etapa (la broca aplica a ambas)
STAGE_FIELDS = {
    QualityStageEnum.cherry: ("ripe_pct", "green_pct", "overripe_pct", "bored_pct"),
    QualityStageEnum.parchment: ("humidity_pct", "defects_pct", "yield_factor", "score", "bored_pct"),
}
FIELD_LABELS = {
    "ripe_pct": "% de maduros",
    "green_pct": "% de verdes",
    "overripe_pct": "% de sobremaduros",
    "bored_pct": "% de brocados",
    "humidity_pct": "% de humedad",
    "defects_pct": "% de defectos",
    "yield_factor": "factor de rendimiento",
    "score": "puntaje",
}


def stage_problem(stage: QualityStageEnum, values: dict) -> Optional[str]:
    """Qué falla en los resultados para la etapa: un campo de otra etapa, o ninguno."""
    own = STAGE_FIELDS[stage]
    for field, label in FIELD_LABELS.items():
        if field not in own and values.get(field) is not None:
            stage_name = "en cereza" if stage == QualityStageEnum.cherry else "en pergamino"
            return f"El {label} no aplica a la evaluación {stage_name}"
    if all(values.get(field) is None for field in own):
        return "Registra al menos un resultado de la evaluación"
    return None


class QualityEvalFields(BaseModel):
    eval_date: date = Field(default_factory=business_today)
    # En cereza
    ripe_pct: Optional[Decimal] = Field(None, **PERCENT)
    green_pct: Optional[Decimal] = Field(None, **PERCENT)
    overripe_pct: Optional[Decimal] = Field(None, **PERCENT)
    bored_pct: Optional[Decimal] = Field(None, description="Aplica a ambas etapas", **PERCENT)
    # En pergamino
    humidity_pct: Optional[Decimal] = Field(None, **PERCENT)
    defects_pct: Optional[Decimal] = Field(None, **PERCENT)
    yield_factor: Optional[Decimal] = Field(None, gt=0, max_digits=6, decimal_places=2, description="Factor de rendimiento en trilla")
    score: Optional[Decimal] = Field(None, description="Puntaje 0–100 estilo SCA", **PERCENT)
    observations: Optional[str] = None

    @field_validator("eval_date")
    @classmethod
    def date_not_in_future(cls, value):
        return not_in_future(value, "La fecha de la evaluación")


class QualityEvalCreate(QualityEvalFields):
    stage: QualityStageEnum
    harvest_id: Optional[int] = Field(None, gt=0, description="Obligatorio en cereza")
    drying_id: Optional[int] = Field(None, gt=0, description="Obligatorio en pergamino")

    @model_validator(mode="after")
    def coherent_stage(self):
        if self.stage == QualityStageEnum.cherry and (self.harvest_id is None or self.drying_id is not None):
            raise ValueError("La evaluación en cereza es de una cosecha")
        if self.stage == QualityStageEnum.parchment and (self.drying_id is None or self.harvest_id is not None):
            raise ValueError("La evaluación en pergamino es de un secado")
        problem = stage_problem(self.stage, self.model_dump())
        if problem:
            raise ValueError(problem)
        return self


class QualityEvalUpdate(QualityEvalFields):
    pass


class QualityEvalResponse(BaseModel):
    id: int
    stage: QualityStageEnum
    harvest_id: Optional[int]
    drying_id: Optional[int]
    eval_date: date
    ripe_pct: Optional[Decimal]
    green_pct: Optional[Decimal]
    overripe_pct: Optional[Decimal]
    bored_pct: Optional[Decimal]
    humidity_pct: Optional[Decimal]
    defects_pct: Optional[Decimal]
    yield_factor: Optional[Decimal]
    score: Optional[Decimal]
    observations: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
