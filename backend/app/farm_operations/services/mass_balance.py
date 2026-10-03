"""
Balance de masas entre etapas (modelo-datos §6.3).

El café que sale de una etapa no puede repartirse en más de lo que hay:

- Cosecha → beneficios: lo aportado por una cosecha no supera su total de
  café cereza. El café se beneficia el mismo día que se recoge, mientras
  la pasada sigue abierta y sin total; por eso el tope se aplica cuando el
  total se conoce: al aportar a una cosecha cerrada y al cerrar o corregir
  el total de una cosecha ya beneficiada.
- Beneficio → secados: lo aportado no supera su café lavado, que se fija al
  completar el beneficio (solo se seca café de beneficios completados).
- Dentro de cada etapa: no sale más café del que entró (café lavado ≤
  cereza; pergamino seco ≤ café lavado).
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError
from app.farm_operations.models import DryingInput, Harvest, WetProcessing, WetProcessingInput
from app.farm_operations.models.enums import HarvestStatusEnum, WetProcessingStatusEnum

ZERO = Decimal(0)


def kg(value: Decimal) -> str:
    """Kilos para mensajes, sin ceros de sobra: 1234,5 kg."""
    text = format(Decimal(value).quantize(Decimal("0.001")).normalize(), "f")
    return f"{text.replace('.', ',')} kg"


def harvest_processed_kg(db: Session, harvest_id: int, exclude_wet_processing_id: Optional[int] = None) -> Decimal:
    """Café cereza de la cosecha ya repartido en beneficios."""
    query = db.query(func.coalesce(func.sum(WetProcessingInput.cherry_kg), 0)).filter(
        WetProcessingInput.harvest_id == harvest_id
    )
    if exclude_wet_processing_id is not None:
        query = query.filter(WetProcessingInput.wet_processing_id != exclude_wet_processing_id)
    return Decimal(query.scalar())


def wet_dried_kg(db: Session, wet_processing_id: int, exclude_drying_id: Optional[int] = None) -> Decimal:
    """Café lavado del beneficio ya repartido en secados."""
    query = db.query(func.coalesce(func.sum(DryingInput.wet_kg), 0)).filter(
        DryingInput.wet_processing_id == wet_processing_id
    )
    if exclude_drying_id is not None:
        query = query.filter(DryingInput.drying_id != exclude_drying_id)
    return Decimal(query.scalar())


def check_harvest_inputs(
    db: Session,
    items: list[tuple[Harvest, Decimal]],
    exclude_wet_processing_id: Optional[int] = None,
) -> None:
    """Lo que se aporta de cada cosecha cerrada cabe en su total."""
    for harvest, cherry_kg in items:
        if harvest.status != HarvestStatusEnum.closed:
            continue
        used = harvest_processed_kg(db, harvest.id, exclude_wet_processing_id)
        available = harvest.total_cherry_kg - used
        if cherry_kg > available:
            raise ConflictError(
                f"La pasada {harvest.pass_number} del lote «{harvest.crop_cycle.plot.name}» tiene "
                f"{kg(harvest.total_cherry_kg)} y ya se benefició {kg(used)}: quedan {kg(max(available, ZERO))}"
            )


def check_harvest_total(db: Session, harvest: Harvest, total: Decimal) -> None:
    """El total de una cosecha no queda por debajo de lo ya beneficiado."""
    used = harvest_processed_kg(db, harvest.id)
    if total < used:
        raise ConflictError(
            f"Ya se benefició {kg(used)} de esta cosecha: el total no puede ser menor"
        )


def check_wet_inputs(
    db: Session,
    items: list[tuple[WetProcessing, Decimal]],
    exclude_drying_id: Optional[int] = None,
) -> None:
    """Solo se seca café de beneficios completados, y no más del lavado que queda."""
    for wet_processing, wet_kg in items:
        if wet_processing.status != WetProcessingStatusEnum.completed:
            raise ConflictError(
                f"El beneficio {wet_processing.id} no está completado: complétalo con su café lavado antes de secar"
            )
        used = wet_dried_kg(db, wet_processing.id, exclude_drying_id)
        available = wet_processing.washed_kg - used
        if wet_kg > available:
            raise ConflictError(
                f"El beneficio {wet_processing.id} tiene {kg(wet_processing.washed_kg)} de café lavado y ya se "
                f"secó {kg(used)}: quedan {kg(max(available, ZERO))}"
            )


def cherry_in(wet_processing: WetProcessing) -> Decimal:
    """Café cereza que entró al beneficio."""
    return sum((item.cherry_kg for item in wet_processing.inputs), ZERO)
