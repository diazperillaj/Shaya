# app/models/maquilado.py
from sqlalchemy import Integer, String, Date, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal

class Processed(Base):
    """
    Modelo ORM que representa el inventario de café maquilado (café procesado).
    
    Almacena detalles del café procesado obtenido a partir de café pergamino,
    incluyendo la relación con el pergamino de origen, peso de bolsas,
    y trazabilidad del proceso de maquila.
    """
    
    __tablename__ = "processed"
    __table_args__ = (
        Index('idx_parchment', 'parchment_id'),
        Index('idx_batch', 'batch'),
        Index('idx_processed_process_date', 'process_date'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inventory_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inventories.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    parchment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parchments.id", ondelete="RESTRICT"),
        nullable=False
    )
    batch: Mapped[str] = mapped_column(String(100), nullable=False)
    bag_weight: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    responsible: Mapped[str] = mapped_column(String(255), nullable=True)
    parchment_weight_used: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    processed_weight_result: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    initial_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    processing_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=True)
    process_date: Mapped[Date] = mapped_column(Date, nullable=False)

    # Relaciones
    inventory = relationship("Inventory", back_populates="processed")
    parchment = relationship("Parchment", back_populates="processed")

    toll_process = relationship(
        "TollProcess",
        foreign_keys="[TollProcess.processed_id]",
        back_populates="processed",
        cascade="all, delete-orphan"
    )
    
    movements = relationship(
        "InventoryMovement",
        foreign_keys="[InventoryMovement.processed_id]",
        back_populates="processed",
        cascade="all, delete-orphan"
    )
    
    sale_details = relationship(
        "SaleDetail",
        foreign_keys="[SaleDetail.processed_id]",
        back_populates="processed",
        cascade="all, delete-orphan"
    )