# app/models/pergamino.py
from sqlalchemy import Integer, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
from decimal import Decimal

class RoastedCoffee(Base):
    """
    Modelo ORM que representa el inventario de café tostado.
    
    Almacena detalles específicos del café tostado, incluyendo características, precio y trazabilidad.
    """
    
    __tablename__ = "roasted_coffees"
    __table_args__ = (
        Index('idx_process_id', 'process_id'),        
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    process_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    observations: Mapped[str] = mapped_column(Text, nullable=True)
            
    process = relationship("Process", back_populates="roasted_coffees")
    details = relationship("DetailRoastedCoffee", back_populates="roasted_coffee", cascade="all, delete-orphan")
            
    