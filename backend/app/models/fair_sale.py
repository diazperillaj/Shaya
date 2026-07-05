from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, Text, func as sql_func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class FairSale(Base):
    __tablename__ = "fair_sales"
    __table_args__ = (
        Index("idx_fair_sale_fair_id", "fair_id"),
        Index("idx_fair_sale_inv_id", "fair_inventory_id"),
        Index("idx_fair_sale_datetime", "sale_datetime"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fair_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fairs.id", ondelete="CASCADE"), nullable=False
    )
    fair_inventory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fair_inventories.id", ondelete="RESTRICT"), nullable=False
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
