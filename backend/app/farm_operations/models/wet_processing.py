from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
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
from app.farm_operations.models.enums import FermentationMethodEnum, WetProcessingStatusEnum


class WetProcessing(Base):
    """
    Beneficio húmedo (modelo-datos §3.14): flotes, despulpado, fermentación
    y lavado.

    Recibe café cereza de una o varias cosechas de la finca (mezclas), con
    los kg que aporta cada una; su salida es el café lavado que va a secado.
    """

    __tablename__ = "wet_processings"
    __table_args__ = (
        CheckConstraint(
            "fermentation_end IS NULL OR (fermentation_start IS NOT NULL AND fermentation_end >= fermentation_start)",
            name="ck_wet_processings_fermentation",
        ),
        CheckConstraint("status != 'completed' OR washed_kg IS NOT NULL", name="ck_wet_processings_completed"),
        Index("idx_wet_processing_farm_id", "farm_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[WetProcessingStatusEnum] = mapped_column(
        Enum(WetProcessingStatusEnum, name="farmwetprocessingstatusenum"),
        nullable=False,
        default=WetProcessingStatusEnum.in_progress,
        server_default=WetProcessingStatusEnum.in_progress.value,
    )
    # 1. Selección de flotes
    floats_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    floats_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # 2. Despulpado
    pulped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # 3. Fermentación
    fermentation_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fermentation_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    fermentation_method: Mapped[Optional[FermentationMethodEnum]] = mapped_column(
        Enum(FermentationMethodEnum, name="farmfermentationmethodenum"), nullable=True
    )
    fermentation_other_detail: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    fermentation_decided_by: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    fermentation_criteria: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ambient_temp_c: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    # 4. Lavado
    wash_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    washed_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)

    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    farm = relationship("Farm")
    inputs = relationship(
        "WetProcessingInput",
        back_populates="wet_processing",
        cascade="all, delete-orphan",
        order_by="WetProcessingInput.id",
    )


class WetProcessingInput(Base):
    """Kg de café cereza que una cosecha aporta a un beneficio (modelo-datos §3.15)."""

    __tablename__ = "wet_processing_inputs"
    __table_args__ = (
        UniqueConstraint("wet_processing_id", "harvest_id", name="uq_wet_processing_inputs_harvest"),
        CheckConstraint("cherry_kg > 0", name="ck_wet_processing_inputs_kg"),
        Index("idx_wp_input_harvest_id", "harvest_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wet_processing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("wet_processings.id", ondelete="CASCADE"), nullable=False
    )
    harvest_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("harvests.id", ondelete="RESTRICT"), nullable=False
    )
    cherry_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    wet_processing = relationship("WetProcessing", back_populates="inputs")
    harvest = relationship("Harvest")
