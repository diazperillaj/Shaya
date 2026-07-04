import enum
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class ProcessExpenseCategoryEnum(enum.Enum):
    """Categorías de gastos adicionales de un proceso de maquila."""
    transport = "transport"
    labor = "labor"
    supplies = "supplies"
    other = "other"


class ProcessExpense(Base):
    """
    Gasto adicional asociado a un proceso de maquila (transporte,
    mano de obra, insumos, etc.).

    El monto es el TOTAL del gasto para el proceso y se prorratea
    por gramos entre todas las bolsas producidas al calcular el
    costo unitario (unit_cost) de los lotes.

    La FK usa RESTRICT: un proceso con gastos no puede eliminarse
    hasta borrar primero sus gastos.
    """

    __tablename__ = "process_expenses"
    __table_args__ = (
        Index("idx_process_expense_process_id", "process_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("processes.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[ProcessExpenseCategoryEnum] = mapped_column(
        Enum(ProcessExpenseCategoryEnum), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    process = relationship("Process", back_populates="expenses")
