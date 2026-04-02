# app/models/inventario.py
from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal

class Inventory(Base):
    """
    Modelo ORM que representa movimientos base de inventario.
    
    Tabla genérica que registra entradas/salidas de productos
    y sirve como base para los detalles específicos de pergamino y maquilado.
    """
    
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )
    date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    observations: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relaciones
    product = relationship("Product", back_populates="inventories")
    
    parchment = relationship(
        "Parchment",
        back_populates="inventory",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    processed = relationship(
        "Processed",
        back_populates="inventory",
        uselist=False,
        cascade="all, delete-orphan"
    )