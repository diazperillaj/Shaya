from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class ExpenseCategory(Base):
    """
    Categoría de gasto general (Bolsas, Nomina, Tostadora, etc.).

    Catálogo administrable desde la UI. La FK de general_expenses usa
    RESTRICT: una categoría con gastos no puede eliminarse.
    """

    __tablename__ = "expense_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    general_expenses = relationship("GeneralExpense", back_populates="category")
