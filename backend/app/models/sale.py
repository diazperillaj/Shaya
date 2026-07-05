import enum
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class SaleStatusEnum(enum.Enum):
    completed = "completed"
    in_progress = "in_progress"


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("idx_sale_customer_id", "customer_id"),
        Index("idx_sale_user_id", "user_id"),
        Index("idx_sale_date", "sale_date"),
        Index("idx_sale_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # Nullable en BD: la venta consolidada de una feria puede mezclar
    # métodos de pago (el desglose real queda en fair_sales). El API
    # sí lo exige para ventas normales.
    payment_method_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment_methods.id", ondelete="RESTRICT"), nullable=True
    )
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[SaleStatusEnum] = mapped_column(
        Enum(SaleStatusEnum), nullable=False, default=SaleStatusEnum.in_progress
    )
    observations: Mapped[str] = mapped_column(Text, nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    customer = relationship("Customer", back_populates="sales")
    payment_method = relationship("PaymentMethod", back_populates="sales")
    user = relationship("User", back_populates="sales")
    details = relationship("DetailSale", back_populates="sale", cascade="all, delete-orphan")
    movements = relationship("InventoryMovement", back_populates="sale", cascade="all, delete-orphan")
