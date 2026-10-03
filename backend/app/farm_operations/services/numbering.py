"""
Numeración legible de ciclos y pasadas (especificacion-api A5).

El número lo asigna el sistema, nunca el cliente: el siguiente al mayor que
ya existe, sin huecos ni duplicados. Lo usan la API y el generador de datos
sintéticos, para que ambos numeren igual.
"""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.farm_operations.models import CropCycle, Harvest


def last_cycle(db: Session, plot_id: int) -> Optional[CropCycle]:
    """Último ciclo del lote, por número."""
    return (
        db.query(CropCycle)
        .filter(CropCycle.plot_id == plot_id)
        .order_by(CropCycle.cycle_number.desc())
        .first()
    )


def next_cycle_number(db: Session, plot_id: int) -> int:
    """Número del ciclo que se abre en el lote: 1, 2, 3…"""
    last = db.query(func.max(CropCycle.cycle_number)).filter(CropCycle.plot_id == plot_id).scalar()
    return (last or 0) + 1


def last_pass_number(db: Session, cycle_id: int) -> Optional[int]:
    """Número de la última pasada del ciclo, si tiene alguna."""
    return db.query(func.max(Harvest.pass_number)).filter(Harvest.crop_cycle_id == cycle_id).scalar()


def next_pass_number(db: Session, cycle_id: int) -> int:
    """Número de la pasada que se abre en el ciclo: 1, 2, 3…"""
    return (last_pass_number(db, cycle_id) or 0) + 1
