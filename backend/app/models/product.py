# app/models/producto.py
from sqlalchemy import Integer, String, Text, Boolean, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base
import enum

class ProductTypeEnum(enum.Enum):
    """Enumeración para tipos de producto"""
    parchment = "parchment"
    processed = "processed"
    other = "other"

class Product(Base):
    """
    Modelo ORM que representa el catálogo general de productos.
    
    Define los tipos de productos disponibles en el sistema
    (café pergamino y café maquilado).
    """
    
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[ProductTypeEnum] = mapped_column(
        Enum(ProductTypeEnum),
        nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relaciones
    inventories = relationship(
        "Inventory",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    
    fast_sales = relationship(
        "FastSale",
        back_populates="product",
        cascade="all, delete-orphan"
    )