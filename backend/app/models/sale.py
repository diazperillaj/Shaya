# app/models/sale.py
from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Enum, Index, func as sql_func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal
import enum


class PaymentTypeEnum(enum.Enum):
    """Enumeración para tipos de pago"""
    cash = "cash"
    transfer = "transfer"
    credit = "credit"


class SaleStatusEnum(enum.Enum):
    """Enumeración para estados de venta"""
    completed = "completed"
    pending = "pending"
    canceled = "canceled"


class Sale(Base):
    """
    Modelo ORM que representa una venta realizada en el sistema.
    
    Registra las ventas de café (pergamino o maquilado) con información
    del cliente, método de pago y estado de la transacción.
    """

    __tablename__ = "sales"
    __table_args__ = (
        Index('idx_sale_date', 'sale_date'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True
    )

    sale_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now()
    )

    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    payment_type: Mapped[PaymentTypeEnum] = mapped_column(
        Enum(PaymentTypeEnum),
        default=PaymentTypeEnum.cash,
        nullable=False
    )

    status: Mapped[SaleStatusEnum] = mapped_column(
        Enum(SaleStatusEnum),
        default=SaleStatusEnum.completed,
        nullable=False
    )

    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relaciones
    customer = relationship("Customer", back_populates="sales")

    sale_details = relationship(
        "SaleDetail",
        back_populates="sale",
        cascade="all, delete-orphan"
    )

    movements = relationship(
        "InventoryMovement",
        foreign_keys="[InventoryMovement.sale_id]",
        back_populates="sale",
        cascade="all, delete-orphan"
    )