from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func as sql_func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class ClimateRecord(Base):
    """
    Registro climático manual (modelo-datos §3.6).

    Es de la finca; con `plot_id` aplica solo a ese lote. No cuelga de los
    ciclos: se asocia a ellos por fecha al consultar, y un registro de la
    finca aplica a todos sus lotes ese día.
    """

    __tablename__ = "climate_records"
    __table_args__ = (
        Index("idx_climate_farm_date", "farm_id", "record_date"),
        Index("idx_climate_plot_id", "plot_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
    )
    plot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="RESTRICT"), nullable=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    rainfall_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)
    temp_min_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    temp_max_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    farm = relationship("Farm")
    plot = relationship("Plot")
