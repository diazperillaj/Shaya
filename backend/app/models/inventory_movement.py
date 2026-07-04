# app/models/movimiento_inventario.py
from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Enum, Index, func as sql_func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal
import enum

class MovementTypeEnum(enum.Enum):
    """Enumeración para tipos de movimiento de inventario"""
    parchment_entrance = "parchment_entrance"
    parchment_exit = "parchment_exit"
    processed_entrance = "processed_entrance"
    processed_exit = "processed_exit"
    adjustment = "adjustment"
    spoilage = "spoilage"
    devolution = "devolution"
    fair_entrance = "fair_entrance"
    fair_return = "fair_return"

class ProductMovementTypeEnum(enum.Enum):
    """Enumeración para tipo de producto en movimiento"""
    parchment = "parchment"
    processed = "processed"

class InventoryMovement(Base):
    """
    Modelo ORM que representa el histórico completo de movimientos de inventario.
    
    Registra cada entrada, salida, ajuste o merma de productos,
    proporcionando trazabilidad completa del inventario.
    """
    
    __tablename__ = "inventory_movements"
    __table_args__ = (
        Index('idx_movement_date', 'movement_date'),
        Index('idx_movement_type', 'movement_type'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movement_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_func.now()
    )
    movement_type: Mapped[MovementTypeEnum] = mapped_column(
        Enum(MovementTypeEnum),
        nullable=False
    )
    product_type: Mapped[ProductMovementTypeEnum] = mapped_column(
        Enum(ProductMovementTypeEnum),
        nullable=False
    )
    parchment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parchments.id", ondelete="CASCADE"),
        nullable=True
    )
    process_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=True
    )
    sale_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=True
    )
    fair_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fairs.id", ondelete="CASCADE"),
        nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=True)


    responsible: Mapped[str] = mapped_column(String(255), nullable=True)
    observations: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relaciones
    parchment = relationship("Parchment", back_populates="movements")
    process = relationship("Process", back_populates="movements")
    sale = relationship("Sale", back_populates="movements")
    fair = relationship("Fair", back_populates="movements")