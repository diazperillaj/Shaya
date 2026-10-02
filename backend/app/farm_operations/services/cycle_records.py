"""
Registros que cuelgan de un ciclo productivo.

Reúne en un solo lugar las labores del ciclo y su columna de fecha, para las
reglas que las miran en conjunto: el rango de fechas de un ciclo debe cubrir
sus labores, un ciclo con labores no se elimina, y el detalle del ciclo
resume cuántas hay de cada tipo.
"""

from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.farm_operations.models import (
    CulturalPractice,
    Fertilization,
    FloweringRecord,
    Irrigation,
    PestMonitoring,
    PhytosanitaryApp,
)

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
    """Primera y última fecha de las labores del ciclo; (None, None) si no tiene."""
    firsts, lasts = [], []
    for model, date_column in CYCLE_LABORS.values():
        first, last = (
            db.query(func.min(date_column), func.max(date_column))
            .filter(model.crop_cycle_id == cycle_id)
            .one()
        )
        if first is not None:
            firsts.append(first)
            lasts.append(last)
    return (min(firsts), max(lasts)) if firsts else (None, None)


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
