from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class GeneralExpense(Base):
    """
    Gasto de la empresa: publicidad, nómina, transporte, créditos, etc.

    Corresponde a la pestaña "Gastos" del Excel original
    (ID, Fecha2, Cantidad, Categoria, Motivo).

    Un gasto puede quedar asociado a un proceso de maquila (`process_id`)
    solo si se crea desde el detalle de ese proceso; la asociación no se
    agrega ni se cambia después. El monto de los gastos asociados se
    prorratea por gramos entre las bolsas del proceso al calcular el
    unit_cost de sus lotes. La FK usa RESTRICT: un proceso con gastos no
    puede eliminarse hasta borrar primero sus gastos.
    """

    __tablename__ = "general_expenses"
    __table_args__ = (
        Index("idx_general_expense_date", "expense_date"),
        Index("idx_general_expense_category_id", "category_id"),
        Index("idx_general_expense_process_id", "process_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=False
    )
    payment_method_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment_methods.id", ondelete="RESTRICT"), nullable=True
    )
    process_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("processes.id", ondelete="RESTRICT"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    category = relationship("ExpenseCategory", back_populates="general_expenses")
    payment_method = relationship("PaymentMethod", back_populates="general_expenses")
    process = relationship("Process", back_populates="expenses")
