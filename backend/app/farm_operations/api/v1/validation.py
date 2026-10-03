"""Validaciones de entrada compartidas por los esquemas del módulo de cultivo."""

from datetime import date, datetime
from typing import Optional

from app.farm_operations.services.dates import BUSINESS_TZ, business_today


def not_in_future(value: Optional[date], what: str) -> Optional[date]:
    """Rechaza fechas posteriores a hoy (en Colombia). `what` nombra la fecha."""
    if value is not None and value > business_today():
        raise ValueError(f"{what} no puede ser futura")
    return value


def moment_not_in_future(value: Optional[datetime], what: str) -> Optional[datetime]:
    """
    Rechaza instantes futuros. Un instante sin zona horaria se entiende en
    hora de Colombia, que es como lo escribe el usuario.
    """
    if value is None:
        return None
    moment = value if value.tzinfo else value.replace(tzinfo=BUSINESS_TZ)
    if moment > datetime.now(BUSINESS_TZ):
        raise ValueError(f"{what} no puede ser futura")
    return moment


def require_other_detail(is_other: bool, detail: Optional[str], message: str) -> None:
    """
    Cuando se elige la opción «otro» de un enum, exige decir cuál.

    `message` es la pregunta para el usuario, p. ej. «Indica cuál labor es».
    """
    if is_other and not (detail or "").strip():
        raise ValueError(message)


def clean_other_detail(is_other: bool, detail: Optional[str]) -> Optional[str]:
    """El detalle solo se guarda con la opción «otro»."""
    return ((detail or "").strip() or None) if is_other else None
