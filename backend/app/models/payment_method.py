from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class PaymentMethod(Base):
    """
    Método/lugar de pago (Efectivo, Nequi, Nu, etc.).

    Catálogo administrable desde la UI. Las FKs que lo referencian usan
    RESTRICT: un método en uso no puede eliminarse.
    """

    __tablename__ = "payment_methods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    sales = relationship("Sale", back_populates="payment_method")
    fair_sales = relationship("FairSale", back_populates="payment_method")
    general_expenses = relationship("GeneralExpense", back_populates="payment_method")
