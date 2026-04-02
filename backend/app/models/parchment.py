# app/models/pergamino.py
from sqlalchemy import Integer, String, Date, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal

class Parchment(Base):
    """
    Modelo ORM que representa el inventario de café pergamino (café seco).
    
    Almacena detalles específicos del café pergamino comprado a caficultores,
    incluyendo características del café, precio de compra y trazabilidad.
    """
    
    __tablename__ = "parchments"
    __table_args__ = (
        Index('idx_farmer', 'farmer_id'),
        Index('idx_purchase_date', 'purchase_date'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inventory_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("inventories.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    farmer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("farmers.id", ondelete="RESTRICT"),
        nullable=False
    )
    variety: Mapped[str] = mapped_column(String(100), nullable=True)
    altitude: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=True)
    humidity: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    full_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    initial_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    purchase_date: Mapped[Date] = mapped_column(Date, nullable=False)
    origin_batch: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Relaciones
    inventory = relationship("Inventory", back_populates="parchment")
    farmer = relationship("Farmer", back_populates="parchments")
    
    processed = relationship(
        "Processed",
        back_populates="parchment",
        cascade="all, delete-orphan"
    )
    
    toll_process = relationship(
        "TollProcess",
        back_populates="parchment",
        cascade="all, delete-orphan"
    )
    
    movements = relationship(
        "InventoryMovement",
        foreign_keys="[InventoryMovement.parchment_id]",
        back_populates="parchment",
        cascade="all, delete-orphan"
    )
    
    sale_details = relationship(
        "SaleDetail",
        foreign_keys="[SaleDetail.parchment_id]",
        back_populates="parchment",
        cascade="all, delete-orphan"
    )