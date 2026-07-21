from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, Text, func as sql_func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class FairSale(Base):
    """
    Venta registrada durante una feria. Puede ser de:
    - inventario asignado a la feria (café: fair_inventory_id), o
    - un producto de feria del catálogo (café preparado, galletas, etc.:
      fair_product_id, sin control de stock).
    Exactamente uno de los dos debe estar presente.
    """

    __tablename__ = "fair_sales"
    __table_args__ = (
        Index("idx_fair_sale_fair_id", "fair_id"),
        Index("idx_fair_sale_inv_id", "fair_inventory_id"),
        Index("idx_fair_sale_product_id", "fair_product_id"),
        Index("idx_fair_sale_datetime", "sale_datetime"),
        CheckConstraint(
            "(fair_inventory_id IS NULL) != (fair_product_id IS NULL)",
            name="ck_fair_sale_item_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fair_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fairs.id", ondelete="CASCADE"), nullable=False
    )
    fair_inventory_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fair_inventories.id", ondelete="RESTRICT"), nullable=True
    )
    fair_product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fair_products.id", ondelete="RESTRICT"), nullable=True
    )
    payment_method_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payment_methods.id", ondelete="RESTRICT"), nullable=False
    )
    sale_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    fair = relationship("Fair", back_populates="fair_sales")
    payment_method = relationship("PaymentMethod", back_populates="fair_sales")
    fair_inventory = relationship("FairInventory", back_populates="fair_sales")
    fair_product = relationship("FairProduct", back_populates="fair_sales")
