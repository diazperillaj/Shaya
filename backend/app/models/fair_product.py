from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class FairProduct(Base):
    """
    Producto de feria (café preparado, galletas, etc.).

    Catálogo administrable desde la UI, con precio por defecto que se
    precarga al registrar una venta (el precio final vive en la venta).
    Las FKs que lo referencian usan RESTRICT: un producto con ventas
    no puede eliminarse.
    """

    __tablename__ = "fair_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    default_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    fair_sales = relationship("FairSale", back_populates="fair_product")
