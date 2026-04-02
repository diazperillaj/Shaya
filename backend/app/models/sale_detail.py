# app/models/detalle_venta.py
from sqlalchemy import Integer, Numeric, ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal
import enum

class SaleProductTypeEnum(enum.Enum):
    """Enumeración para tipo de producto en venta"""
    parchment = "parchment"
    processed = "processed"

class SaleDetail(Base):
    """
    Modelo ORM que representa el detalle de una venta (línea de venta).
    
    Cada línea puede corresponder a café pergamino o café maquilado,
    manteniendo la trazabilidad del producto vendido.
    """
    
    __tablename__ = "sale_details"
    __table_args__ = (
        CheckConstraint(
            """
            (product_type = 'parchment' AND parchment_id IS NOT NULL AND processed_id IS NULL) OR
            (product_type = 'processed' AND processed_id IS NOT NULL AND parchment_id IS NULL)
            """,
            name="check_product_type_consistency"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False
    )
    product_type: Mapped[SaleProductTypeEnum] = mapped_column(
        Enum(SaleProductTypeEnum),
        nullable=False
    )
    parchment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parchments.id", ondelete="RESTRICT"),
        nullable=True
    )
    processed_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processed.id", ondelete="RESTRICT"),
        nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Relaciones
    sale = relationship("Sale", back_populates="sale_details")
    parchment = relationship("Parchment", back_populates="sale_details")
    processed = relationship("Processed", back_populates="sale_details")