"""
Utilidades comunes de la capa analytics.

Esta capa es PURA: no conoce FastAPI ni el LLM. Recibe parámetros tipados,
consulta el negocio con SQL filtrado (usuario de solo lectura) y agrega con
Pandas. Toda función devuelve dicts compactos: {"resumen", "filas", "advertencias"}.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import text

from app.core.db import business_engine

BOGOTA = ZoneInfo("America/Bogota")

DEFAULT_TOP = 10
MAX_TOP = 50
MAX_RANGE_MONTHS = 24


class ToolError(Exception):
    """
    Error accionable para el LLM: el mensaje se devuelve como tool_result
    con is_error=true para que el modelo se autocorrija o informe al usuario
    ("la venta 999 no existe"). Nunca produce un 500.
    """


def now_bogota() -> datetime:
    return datetime.now(tz=BOGOTA)


@dataclass
class DateRange:
    """Rango efectivo aplicado: [start, end) — semiabierto."""

    start: datetime | None
    end: datetime | None
    has_time: bool = False           # el usuario pidió precisión horaria
    warnings: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        if not self.start and not self.end:
            return "todo el histórico"
        fmt = "%Y-%m-%d %H:%M" if self.has_time else "%Y-%m-%d"
        ini = self.start.strftime(fmt) if self.start else "inicio"
        fin = self.end.strftime(fmt) if self.end else "hoy"
        return f"{ini} → {fin}"

    def date_bounds(self) -> tuple[date | None, date | None]:
        """
        Cotas para columnas DATE (sin hora): [d0, d1) en días completos.
        Si el rango traía hora, se expande al día completo y se advierte.
        """
        d0 = self.start.date() if self.start else None
        d1 = self.end.date() if self.end else None
        if self.end and (self.end.time() != datetime.min.time()):
            d1 = self.end.date() + timedelta(days=1)
        return d0, d1


def _parse_dt(value: str, campo: str) -> tuple[datetime, bool]:
    """Acepta YYYY-MM-DD, YYYY-MM-DDTHH:MM o YYYY-MM-DDTHH:MM:SS (TZ Bogotá)."""
    value = value.strip()
    for fmt, has_time in (
        ("%Y-%m-%dT%H:%M:%S", True),
        ("%Y-%m-%dT%H:%M", True),
        ("%Y-%m-%d %H:%M:%S", True),
        ("%Y-%m-%d %H:%M", True),
        ("%Y-%m-%d", False),
    ):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=BOGOTA), has_time
        except ValueError:
            continue
    raise ToolError(
        f"Formato de fecha inválido en {campo}: '{value}'. "
        "Usa YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS."
    )


def parse_range(fecha_inicio: str | None, fecha_fin: str | None) -> DateRange:
    """
    Normaliza el rango pedido por el LLM. Reglas:
    - Ambos None → sin filtro (todo el histórico; el volumen actual lo permite).
    - fecha_fin solo-fecha → inclusiva (se expande al final del día).
    - Intervalo semiabierto [inicio, fin).
    """
    start = end = None
    has_time = False
    warnings: list[str] = []

    if fecha_inicio:
        start, t0 = _parse_dt(fecha_inicio, "fecha_inicio")
        has_time = has_time or t0
    if fecha_fin:
        end, t1 = _parse_dt(fecha_fin, "fecha_fin")
        if not t1:
            end = end + timedelta(days=1)  # día final inclusivo
        has_time = has_time or t1

    if start and end and start >= end:
        raise ToolError(
            f"El rango es inválido: fecha_inicio ({fecha_inicio}) debe ser "
            f"anterior a fecha_fin ({fecha_fin})."
        )
    if start and end and (end - start) > timedelta(days=31 * MAX_RANGE_MONTHS):
        warnings.append(f"Rango mayor a {MAX_RANGE_MONTHS} meses; puede ser lento.")

    return DateRange(start=start, end=end, has_time=has_time, warnings=warnings)


def read_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Ejecuta SQL de solo lectura sobre el negocio y devuelve un DataFrame."""
    with business_engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def clamp_top(top: int | None) -> int:
    if not top or top < 1:
        return DEFAULT_TOP
    return min(top, MAX_TOP)


def num(value: Any, decimals: int = 2) -> float | int | None:
    """Redondeo homogéneo para la salida (dinero 2 decimales, % 1)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float):
        rounded = round(value, decimals)
        return int(rounded) if rounded == int(rounded) and decimals == 0 else rounded
    return value


def df_to_rows(df: pd.DataFrame, top: int) -> tuple[list[dict], bool]:
    """Convierte el DF agregado en filas JSON compactas, con tope duro."""
    truncated = len(df) > top
    rows: list[dict] = []
    for _, row in df.head(top).iterrows():
        clean: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (Decimal, float)):
                clean[key] = num(value)
            elif isinstance(value, (pd.Timestamp, datetime, date)):
                clean[key] = str(value)[:19]
            elif pd.isna(value):
                clean[key] = None
            else:
                clean[key] = value
        rows.append(clean)
    return rows, truncated


def result(
    resumen: dict[str, Any],
    filas: list[dict] | None = None,
    advertencias: list[str] | None = None,
) -> dict[str, Any]:
    """Contrato único de salida de toda función analítica."""
    out: dict[str, Any] = {"resumen": resumen}
    if filas:
        out["filas"] = filas
    if advertencias:
        out["advertencias"] = advertencias
    return out


def add_month_column(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    df["mes"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m")
    return df


def add_week_column(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    iso = pd.to_datetime(df[date_col]).dt.isocalendar()
    df["semana"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
    return df
