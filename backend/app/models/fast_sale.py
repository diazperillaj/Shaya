from sqlalchemy import Integer, Text, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base

class FastSale(Base):
    """
    Modelo ORM que representa una venta rápida.
    """
    __tablename__ = "fast_sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    description: Mapped[str] = mapped_column(Text, nullable=True)

    product = relationship("Product", back_populates="fast_sales")
    user = relationship("User", back_populates="fast_sales")