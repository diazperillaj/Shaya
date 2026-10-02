from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func as sql_func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import CycleStatusEnum


class CropCycle(Base):
    """
    Ciclo productivo de un lote (modelo-datos §3.5).

    Agrupa las labores, cosechas y beneficios de una temporada. Un lote tiene
    a lo sumo un ciclo activo; `cycle_number` lo numera dentro del lote
    (1, 2, 3…) para reconocerlo en pantallas y reportes.
    """

    __tablename__ = "crop_cycles"
    __table_args__ = (
        UniqueConstraint("plot_id", "cycle_number", name="uq_crop_cycles_plot_number"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_crop_cycles_dates",
        ),
        # Cerrado ⇔ con fecha de fin: reabrir un ciclo le quita la fecha
        CheckConstraint(
            "(status = 'closed') = (end_date IS NOT NULL)",
            name="ck_crop_cycles_end_date_status",
        ),
        Index(
            "uq_crop_cycles_one_active",
            "plot_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("idx_crop_cycle_plot_id", "plot_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="RESTRICT"), nullable=False
    )
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[CycleStatusEnum] = mapped_column(
        Enum(CycleStatusEnum, name="farmcyclestatusenum"),
        nullable=False,
        default=CycleStatusEnum.active,
        server_default=CycleStatusEnum.active.value,
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    plot = relationship("Plot")
