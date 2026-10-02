"""
Tipos de labor del ciclo.

Las seis labores comparten las mismas operaciones y reglas (especificacion-api
§3.5); cada `LaborKind` declara solo lo que las distingue: esquemas, cómo
normalizar sus textos y si admite el registro en varios lotes. El modelo y
su columna de fecha salen de `CYCLE_LABORS`. El servicio y las rutas
genéricas hacen el resto.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from pydantic import BaseModel

from app.farm_operations.api.v1.labors import schema
from app.farm_operations.api.v1.validation import clean_other_detail
from app.farm_operations.models.enums import CulturalPracticeTypeEnum
from app.farm_operations.services.cycle_records import CYCLE_LABORS


def strip_texts(*fields: str) -> Callable[[dict], dict]:
    """Normaliza textos libres: sin espacios sobrantes y vacío = None."""

    def normalize(data: dict) -> dict:
        for field in fields:
            data[field] = (data.get(field) or "").strip() or None
        return data

    return normalize


def normalize_cultural_practice(data: dict) -> dict:
    is_other = data["practice_type"] == CulturalPracticeTypeEnum.other
    data["other_detail"] = clean_other_detail(is_other, data.get("other_detail"))
    return data


@dataclass(frozen=True)
class LaborKind:
    path: str
    """Segmento de la ruta y clave en `CYCLE_LABORS`: `fertilizations`."""
    label: str
    """Nombre en plural para la documentación de la API."""
    create_schema: type[BaseModel]
    update_schema: type[BaseModel]
    response_schema: type[BaseModel]
    bulk_schema: Optional[type[BaseModel]] = None
    """Solo las labores que se hacen igual en varios lotes."""
    normalize: Callable[[dict], dict] = lambda data: data

    @property
    def model(self) -> type:
        return CYCLE_LABORS[self.path][0]

    @property
    def date_column(self):
        return CYCLE_LABORS[self.path][1]

    @property
    def date_field(self) -> str:
        return self.date_column.key


LABOR_KINDS = (
    LaborKind(
        path="fertilizations",
        label="Fertilizaciones",
        create_schema=schema.FertilizationCreate,
        update_schema=schema.FertilizationUpdate,
        response_schema=schema.FertilizationResponse,
        bulk_schema=schema.FertilizationBulk,
    ),
    LaborKind(
        path="phytosanitary-apps",
        label="Aplicaciones fitosanitarias",
        create_schema=schema.PhytosanitaryCreate,
        update_schema=schema.PhytosanitaryUpdate,
        response_schema=schema.PhytosanitaryResponse,
        bulk_schema=schema.PhytosanitaryBulk,
        normalize=strip_texts("target", "dose_description"),
    ),
    LaborKind(
        path="irrigations",
        label="Riegos",
        create_schema=schema.IrrigationCreate,
        update_schema=schema.IrrigationUpdate,
        response_schema=schema.IrrigationResponse,
        bulk_schema=schema.IrrigationBulk,
        normalize=strip_texts("method"),
    ),
    LaborKind(
        path="pest-monitorings",
        label="Monitoreos de plagas",
        create_schema=schema.PestMonitoringCreate,
        update_schema=schema.PestMonitoringUpdate,
        response_schema=schema.PestMonitoringResponse,
        normalize=strip_texts("other_pest"),
    ),
    LaborKind(
        path="cultural-practices",
        label="Labores culturales",
        create_schema=schema.CulturalPracticeCreate,
        update_schema=schema.CulturalPracticeUpdate,
        response_schema=schema.CulturalPracticeResponse,
        bulk_schema=schema.CulturalPracticeBulk,
        normalize=normalize_cultural_practice,
    ),
    LaborKind(
        path="flowering-records",
        label="Floraciones",
        create_schema=schema.FloweringCreate,
        update_schema=schema.FloweringUpdate,
        response_schema=schema.FloweringResponse,
        bulk_schema=schema.FloweringBulk,
    ),
)
