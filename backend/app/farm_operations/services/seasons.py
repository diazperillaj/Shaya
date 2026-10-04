"""
Temporadas de cosecha (dashboards-alertas §2.1).

Una temporada es un grupo de cosechas (pasadas) tal que entre una y la
siguiente no pasan más de `SEASON_GAP_DAYS` días sin recolección. Es lo que
el caficultor llama «la cosecha» (la principal, la mitaca), no una pasada
suelta. Alimenta los botones «Última(s) N cosecha(s)» del dashboard: el
frontend solo toma sus fechas, sin repetir esta lógica.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, Optional

SEASON_GAP_DAYS = 45

MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]


@dataclass
class HarvestSpan:
    start: date
    end: Optional[date]                     # None = abierta
    cherry_kg: Optional[Decimal]
    last_work: Optional[date] = None        # última recolección registrada


@dataclass
class Season:
    date_from: date
    date_to: date
    harvests: int
    cherry_kg: Decimal
    open: bool

    @property
    def label(self) -> str:
        start, end = self.date_from, self.date_to
        if start.year == end.year and start.month == end.month:
            months = MONTHS[start.month - 1]
        else:
            months = f"{MONTHS[start.month - 1]}–{MONTHS[end.month - 1]}"
        return f"Cosecha {months} {end.year}"


def activity_end(span: HarvestSpan) -> date:
    """Hasta dónde llega la actividad de una pasada: su cierre o, abierta, su última recolección."""
    if span.end is not None:
        return span.end
    return max(d for d in (span.start, span.last_work) if d is not None)


def group_seasons(spans: Iterable[HarvestSpan], today: date) -> list[Season]:
    """
    Agrupa las cosechas en temporadas, la más reciente primero.

    Una pasada abierta cuenta hasta su última recolección: una que se olvidó
    cerrar no une temporadas. La temporada en curso (con una pasada abierta y
    recolección reciente) llega hasta hoy.
    """
    ordered = sorted(spans, key=lambda span: span.start)
    seasons: list[Season] = []
    for span in ordered:
        end = activity_end(span)
        kg = span.cherry_kg or Decimal(0)
        current = seasons[-1] if seasons else None
        if current is not None and span.start <= current.date_to + timedelta(days=SEASON_GAP_DAYS):
            current.date_to = max(current.date_to, end)
            current.harvests += 1
            current.cherry_kg += kg
            current.open = current.open or span.end is None
        else:
            seasons.append(Season(span.start, end, 1, kg, span.end is None))
    if seasons and seasons[-1].open and today - seasons[-1].date_to <= timedelta(days=SEASON_GAP_DAYS):
        seasons[-1].date_to = today
    return list(reversed(seasons))
