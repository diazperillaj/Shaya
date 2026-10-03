"""
Registros que cuelgan de un ciclo productivo.

Reúne en un solo lugar las labores del ciclo y su columna de fecha, para las
reglas que las miran en conjunto: el rango de fechas de un ciclo debe cubrir
sus labores y sus cosechas, un ciclo con registros no se elimina, y el
detalle del ciclo resume cuántas labores hay de cada tipo.
"""

from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.farm_operations.models import (
    CulturalPractice,
    Fertilization,
    FloweringRecord,
    Harvest,
    HarvestWork,
    Irrigation,
    PestMonitoring,
    PhytosanitaryApp,
)
from app.farm_operations.models.enums import HarvestStatusEnum

# Tipo de labor → (modelo, columna de fecha). La clave es la de la API.
CYCLE_LABORS = {
    "fertilizations": (Fertilization, Fertilization.application_date),
    "phytosanitary-apps": (PhytosanitaryApp, PhytosanitaryApp.application_date),
    "irrigations": (Irrigation, Irrigation.irrigation_date),
    "pest-monitorings": (PestMonitoring, PestMonitoring.monitoring_date),
    "cultural-practices": (CulturalPractice, CulturalPractice.practice_date),
    "flowering-records": (FloweringRecord, FloweringRecord.flowering_date),
}


def record_date_bounds(db: Session, cycle_id: int) -> tuple[Optional[date], Optional[date]]:
    """
    Primera y última fecha de los registros del ciclo: labores, cosechas y su
    recolección. (None, None) si no tiene ninguno.
    """
    firsts, lasts = [], []

    def add(first: Optional[date], last: Optional[date]) -> None:
        if first is not None:
            firsts.append(first)
        if last is not None:
            lasts.append(last)

    for model, date_column in CYCLE_LABORS.values():
        add(*db.query(func.min(date_column), func.max(date_column)).filter(model.crop_cycle_id == cycle_id).one())

    add(*db.query(
        func.min(Harvest.start_date), func.max(func.coalesce(Harvest.end_date, Harvest.start_date))
    ).filter(Harvest.crop_cycle_id == cycle_id).one())
    add(None, db.query(func.max(HarvestWork.work_date))
        .join(Harvest, HarvestWork.harvest_id == Harvest.id)
        .filter(Harvest.crop_cycle_id == cycle_id)
        .scalar())

    return (min(firsts) if firsts else None, max(lasts) if lasts else None)


def open_harvest(db: Session, cycle_id: int) -> Optional[Harvest]:
    """Cosecha abierta del ciclo, si la hay (a lo sumo una)."""
    return (
        db.query(Harvest)
        .filter(Harvest.crop_cycle_id == cycle_id, Harvest.status == HarvestStatusEnum.open)
        .first()
    )


def records_summary(db: Session, cycle_id: int) -> list[dict]:
    """Por tipo de labor: cuántas hay, la última fecha y el costo total (si aplica)."""
    summary = []
    for kind, (model, date_column) in CYCLE_LABORS.items():
        has_cost = hasattr(model, "cost")
        columns = [func.count(model.id), func.max(date_column)]
        if has_cost:
            columns.append(func.sum(model.cost))
        row = db.query(*columns).filter(model.crop_cycle_id == cycle_id).one()
        summary.append({
            "kind": kind,
            "count": row[0],
            "last_date": row[1],
            "total_cost": row[2] if has_cost else None,
        })
    return summary
