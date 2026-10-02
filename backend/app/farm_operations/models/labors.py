"""
Labores del ciclo y análisis de suelo (modelo-datos §3.8).

Cada labor pertenece a un ciclo (`crop_cycle_id`): así el análisis atribuye
lo hecho en cada lote a su temporada. El análisis de suelo es la excepción:
el suelo es del terreno, así que cuelga del lote y se asocia a los ciclos por
fecha.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import (
    CulturalPracticeTypeEnum,
    FertilizationMethodEnum,
    IntensityEnum,
    SeverityEnum,
)


def cycle_fk() -> Mapped[int]:
    return mapped_column(Integer, ForeignKey("crop_cycles.id", ondelete="RESTRICT"), nullable=False)


def supply_fk() -> Mapped[int]:
    return mapped_column(Integer, ForeignKey("supplies.id", ondelete="RESTRICT"), nullable=False)


def created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=sql_func.now())


class Fertilization(Base):
    """Fertilización edáfica o foliar, con el insumo y la cantidad aplicada al lote."""

    __tablename__ = "fertilizations"
    __table_args__ = (Index("idx_fertilization_cycle_date", "crop_cycle_id", "application_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = cycle_fk()
    supply_id: Mapped[int] = supply_fk()
    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[FertilizationMethodEnum] = mapped_column(
        Enum(FertilizationMethodEnum, name="farmfertilizationmethodenum"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    dose_per_tree_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    crop_cycle = relationship("CropCycle")
    supply = relationship("Supply")


class PhytosanitaryApp(Base):
    """Aplicación de un producto contra una plaga, enfermedad o maleza."""

    __tablename__ = "phytosanitary_apps"
    __table_args__ = (Index("idx_phytosanitary_cycle_date", "crop_cycle_id", "application_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = cycle_fk()
    supply_id: Mapped[int] = supply_fk()
    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    target: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    dose_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    crop_cycle = relationship("CropCycle")
    supply = relationship("Supply")


class Irrigation(Base):
    """Riego del lote."""

    __tablename__ = "irrigations"
    __table_args__ = (Index("idx_irrigation_cycle_date", "crop_cycle_id", "irrigation_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = cycle_fk()
    irrigation_date: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    volume_liters: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 1), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    crop_cycle = relationship("CropCycle")


class PestMonitoring(Base):
    """Muestreo de plagas y enfermedades: % de broca, de roya u otra plaga."""

    __tablename__ = "pest_monitorings"
    __table_args__ = (Index("idx_pest_monitoring_cycle_date", "crop_cycle_id", "monitoring_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = cycle_fk()
    monitoring_date: Mapped[date] = mapped_column(Date, nullable=False)
    broca_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    roya_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    other_pest: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    other_pest_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    severity: Mapped[Optional[SeverityEnum]] = mapped_column(
        Enum(SeverityEnum, name="farmseverityenum"), nullable=True
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    crop_cycle = relationship("CropCycle")


class CulturalPractice(Base):
    """Labor cultural: deshierba, poda, regulación de sombrío, encalado u otra."""

    __tablename__ = "cultural_practices"
    __table_args__ = (Index("idx_cultural_practice_cycle_date", "crop_cycle_id", "practice_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = cycle_fk()
    practice_type: Mapped[CulturalPracticeTypeEnum] = mapped_column(
        Enum(CulturalPracticeTypeEnum, name="farmculturalpracticetypeenum"), nullable=False
    )
    other_detail: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    practice_date: Mapped[date] = mapped_column(Date, nullable=False)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    crop_cycle = relationship("CropCycle")


class FloweringRecord(Base):
    """Floración observada; la principal permite estimar la cosecha (~32 semanas)."""

    __tablename__ = "flowering_records"
    __table_args__ = (Index("idx_flowering_cycle_date", "crop_cycle_id", "flowering_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = cycle_fk()
    flowering_date: Mapped[date] = mapped_column(Date, nullable=False)
    intensity: Mapped[IntensityEnum] = mapped_column(
        Enum(IntensityEnum, name="farmintensityenum"), nullable=False
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    crop_cycle = relationship("CropCycle")


class SoilAnalysis(Base):
    """Análisis de suelo de laboratorio. Es del terreno: cuelga del lote."""

    __tablename__ = "soil_analyses"
    __table_args__ = (Index("idx_soil_analysis_plot_date", "plot_id", "analysis_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="RESTRICT"), nullable=False
    )
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    ph: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    organic_matter_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    nitrogen: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    phosphorus: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    potassium: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    texture: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    laboratory: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = created_at()

    plot = relationship("Plot")
