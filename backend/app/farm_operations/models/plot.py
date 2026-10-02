from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func as sql_func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import PlotEventTypeEnum, PlotStatusEnum


class Plot(Base):
    """
    Lote: un terreno de la finca y su única siembra (modelo-datos §3.2).

    El cierre es definitivo cuando el lote deja de dar cosecha; reabrirlo
    solo corrige un cierre por error. Sembrar de nuevo el terreno crea un
    lote nuevo, enlazado al anterior con `renewed_from_plot_id`.
    """

    __tablename__ = "plots"
    __table_args__ = (
        CheckConstraint(
            "planting_date IS NOT NULL OR initial_age_years IS NOT NULL",
            name="ck_plots_planting_or_age",
        ),
        CheckConstraint(
            "status != 'closed' OR closed_at IS NOT NULL",
            name="ck_plots_closed_has_date",
        ),
        # El nombre se puede reutilizar cuando el lote anterior está cerrado
        Index(
            "uq_plots_farm_name_active",
            "farm_id",
            "name",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("idx_plot_farm_id", "farm_id"),
        Index("idx_plot_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[PlotStatusEnum] = mapped_column(
        Enum(PlotStatusEnum, name="farmplotstatusenum"),
        nullable=False,
        default=PlotStatusEnum.active,
        server_default=PlotStatusEnum.active.value,
    )
    renewed_from_plot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="RESTRICT"), nullable=True
    )

    # Terreno
    area: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    slope: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    soil_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Siembra
    variety: Mapped[str] = mapped_column(String(100), nullable=False)
    planting_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    initial_age_years: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    seedling_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    row_spacing_m: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    plant_spacing_m: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    shade_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Procedencia de la semilla
    seed_supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seed_origin_place: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seed_purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    seed_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    closed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    farm = relationship("Farm", back_populates="plots")
    renewed_from = relationship("Plot", remote_side=[id])
    events = relationship(
        "PlotEvent",
        back_populates="plot",
        order_by="(PlotEvent.event_date.desc(), PlotEvent.id.desc())",
    )


class PlotEvent(Base):
    """
    Evento fechado en el historial de un lote (modelo-datos §3.3).

    Todo cambio relevante queda como evento: zoca, resiembra parcial, cambio
    de sombrío, cierre y reapertura.
    """

    __tablename__ = "plot_events"
    __table_args__ = (
        Index("idx_plot_event_plot_id", "plot_id"),
        Index("idx_plot_event_date", "event_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[PlotEventTypeEnum] = mapped_column(
        Enum(PlotEventTypeEnum, name="farmploteventtypeenum"), nullable=False
    )
    other_detail: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    plot = relationship("Plot", back_populates="events")
