# app/models/pergamino.py
from typing import Optional

from sqlalchemy import Integer, Numeric, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal

class DetailRoastedCoffee(Base):
    """
    Modelo ORM que representa el inventario de café tostado.
    
    Almacena detalles específicos del café tostado, incluyendo características, precio y trazabilidad.
    """
    
    __tablename__ = "detail_roasted_coffees"
    __table_args__ = (
        Index('idx_roasted_coffee_id', 'roasted_coffee_id'),        
        Index('idx_product_id', 'product_id'),        
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    roasted_coffee_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roasted_coffees.id", ondelete="CASCADE"),
        nullable=False
    )
            
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False
    )
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Costo por bolsa congelado al momento del proceso:
    # pergamino + gastos del proceso (prorrateados) + maquila con IVA
    # + costos de producción del producto. NULL = aún no calculado.
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    
    roasted_coffee = relationship("RoastedCoffee", back_populates="details")
    product = relationship("Product", back_populates="roasted_coffee_details")
    sale_details = relationship("DetailSale", back_populates="detail_roasted_coffee")
    fair_inventories = relationship("FairInventory", back_populates="detail_roasted_coffee")
    