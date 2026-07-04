import enum
from decimal import Decimal
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class ProductExpenseCategoryEnum(enum.Enum):
    """Categorías de costos de producción por bolsa de un producto."""
    packaging = "packaging"
    label = "label"
    supplies = "supplies"
    other = "other"


class ProductExpense(Base):
    """
    Costo de producción asociado a un producto del catálogo
    (empaque, etiqueta, insumos, etc.).

    El monto es POR BOLSA y se suma directo al costo unitario
    (unit_cost) de cada bolsa del producto en los procesos que se
    creen a partir de su registro. Los lotes ya producidos conservan
    su costo histórico.
    """

    __tablename__ = "product_expenses"
    __table_args__ = (
        Index("idx_product_expense_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[ProductExpenseCategoryEnum] = mapped_column(
        Enum(ProductExpenseCategoryEnum), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    product = relationship("Product", back_populates="expenses")
