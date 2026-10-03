from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    false,
    func as sql_func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import HarvestPaymentTypeEnum, HarvestStatusEnum


class Harvest(Base):
    """
    Cosecha: una pasada de recolección por el lote (modelo-datos §3.10).

    Funciona como una sesión, igual que las ferias: se abre, se registra la
    recolección de cada día y se cierra con el total de café cereza. La
    composición de la cosecha vive en `quality_evals` (etapa `cherry`).
    """

    __tablename__ = "harvests"
    __table_args__ = (
        UniqueConstraint("crop_cycle_id", "pass_number", name="uq_harvests_cycle_pass"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_harvests_dates"),
        # Cerrada ⇔ con fecha de fin; al cerrar queda su total de cereza
        CheckConstraint("(status = 'closed') = (end_date IS NOT NULL)", name="ck_harvests_end_date_status"),
        CheckConstraint("status != 'closed' OR total_cherry_kg IS NOT NULL", name="ck_harvests_closed_total"),
        Index("idx_harvest_cycle_id", "crop_cycle_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crop_cycle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crop_cycles.id", ondelete="RESTRICT"), nullable=False
    )
    pass_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[HarvestStatusEnum] = mapped_column(
        Enum(HarvestStatusEnum, name="farmharveststatusenum"),
        nullable=False,
        default=HarvestStatusEnum.open,
        server_default=HarvestStatusEnum.open.value,
    )
    rate_per_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    rate_per_day: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    total_cherry_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    crop_cycle = relationship("CropCycle")
    works = relationship(
        "HarvestWork",
        back_populates="harvest",
        cascade="all, delete-orphan",
        order_by="(HarvestWork.work_date.desc(), HarvestWork.id.desc())",
    )


class HarvestWork(Base):
    """
    Recolección de un empleado en un día (modelo-datos §3.11).

    Se paga al peso (kg × tarifa) o por jornal; el valor a pagar se calcula
    al guardar y queda almacenado, igual que el estado de pago.
    """

    __tablename__ = "harvest_works"
    __table_args__ = (
        CheckConstraint(
            "(payment_type = 'per_kg' AND kg_collected IS NOT NULL AND rate_per_kg IS NOT NULL)"
            " OR (payment_type = 'per_day' AND day_value IS NOT NULL)",
            name="ck_harvest_works_payment",
        ),
        CheckConstraint("paid = (paid_at IS NOT NULL)", name="ck_harvest_works_paid"),
        Index("idx_hwork_harvest_date", "harvest_id", "work_date"),
        Index("idx_hwork_employee_id", "employee_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    harvest_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("harvests.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[HarvestPaymentTypeEnum] = mapped_column(
        Enum(HarvestPaymentTypeEnum, name="farmharvestpaymenttypeenum"),
        nullable=False,
        default=HarvestPaymentTypeEnum.per_kg,
        server_default=HarvestPaymentTypeEnum.per_kg.value,
    )
    kg_collected: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    rate_per_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    day_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    paid_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    harvest = relationship("Harvest", back_populates="works")
    employee = relationship("Employee")
