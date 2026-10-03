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
    String,
    Text,
    false,
    func as sql_func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import LaborActivityEnum


class DayLabor(Base):
    """
    Jornal: un día de trabajo pagado que no es recolección (modelo-datos §3.12).

    Cuelga del empleado (y por él, de su finca); el lote donde trabajó es
    opcional.
    """

    __tablename__ = "day_labors"
    __table_args__ = (
        CheckConstraint("paid = (paid_at IS NOT NULL)", name="ck_day_labors_paid"),
        Index("idx_day_labor_employee_date", "employee_id", "labor_date"),
        Index("idx_day_labor_plot_id", "plot_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    labor_date: Mapped[date] = mapped_column(Date, nullable=False)
    activity_type: Mapped[LaborActivityEnum] = mapped_column(
        Enum(LaborActivityEnum, name="farmlaboractivityenum"), nullable=False
    )
    other_detail: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    plot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="RESTRICT"), nullable=True
    )
    daily_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())
    paid_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    employee = relationship("Employee")
    plot = relationship("Plot")
