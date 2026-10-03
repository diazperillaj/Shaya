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
    UniqueConstraint,
    func as sql_func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import DryingDestinationEnum, DryingMethodEnum, DryingStatusEnum


class Drying(Base):
    """
    Secado y almacenamiento (modelo-datos §3.16).

    Recibe café lavado de uno o varios beneficios de la finca. Al cerrarse
    queda el pergamino seco, su empaque y su destino; con destino inventario
    crea el registro de `parchments` que lo enlaza (`parchments.drying_id`).
    La relación se declara solo desde este lado: el inventario no conoce el
    módulo de cultivo.
    """

    __tablename__ = "dryings"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_dryings_dates"),
        CheckConstraint("(status = 'completed') = (end_date IS NOT NULL)", name="ck_dryings_end_date_status"),
        CheckConstraint(
            "status != 'completed' OR (output_kg IS NOT NULL AND final_humidity_pct IS NOT NULL"
            " AND destination IS NOT NULL)",
            name="ck_dryings_completed_fields",
        ),
        Index("idx_drying_farm_id", "farm_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[DryingStatusEnum] = mapped_column(
        Enum(DryingStatusEnum, name="farmdryingstatusenum"),
        nullable=False,
        default=DryingStatusEnum.in_progress,
        server_default=DryingStatusEnum.in_progress.value,
    )
    method: Mapped[DryingMethodEnum] = mapped_column(
        Enum(DryingMethodEnum, name="farmdryingmethodenum"), nullable=False
    )
    other_detail: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    final_humidity_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    output_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    # Almacenamiento (al cierre)
    packaging: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    sack_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    packed_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    storage_place: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    destination: Mapped[Optional[DryingDestinationEnum]] = mapped_column(
        Enum(DryingDestinationEnum, name="farmdryingdestinationenum"), nullable=True
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    farm = relationship("Farm")
    inputs = relationship(
        "DryingInput", back_populates="drying", cascade="all, delete-orphan", order_by="DryingInput.id"
    )
    humidity_checks = relationship(
        "DryingHumidityCheck",
        back_populates="drying",
        cascade="all, delete-orphan",
        order_by="(DryingHumidityCheck.check_date, DryingHumidityCheck.id)",
    )
    parchment = relationship("Parchment", uselist=False, viewonly=True)


class DryingInput(Base):
    """Kg de café lavado que un beneficio aporta a un secado (modelo-datos §3.17)."""

    __tablename__ = "drying_inputs"
    __table_args__ = (
        UniqueConstraint("drying_id", "wet_processing_id", name="uq_drying_inputs_wet_processing"),
        CheckConstraint("wet_kg > 0", name="ck_drying_inputs_kg"),
        Index("idx_drying_input_wet_processing_id", "wet_processing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drying_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dryings.id", ondelete="CASCADE"), nullable=False
    )
    wet_processing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wet_processings.id", ondelete="RESTRICT"), nullable=False
    )
    wet_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    drying = relationship("Drying", back_populates="inputs")
    wet_processing = relationship("WetProcessing")


class DryingHumidityCheck(Base):
    """Medición intermedia de humedad durante el secado."""

    __tablename__ = "drying_humidity_checks"
    __table_args__ = (
        CheckConstraint("humidity_pct >= 0 AND humidity_pct <= 100", name="ck_drying_humidity_checks_range"),
        Index("idx_humidity_check_drying_id", "drying_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drying_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dryings.id", ondelete="CASCADE"), nullable=False
    )
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    humidity_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    drying = relationship("Drying", back_populates="humidity_checks")
