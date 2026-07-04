from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class DetailSale(Base):
    __tablename__ = "detail_sales"
    __table_args__ = (
        Index("idx_detail_sale_sale_id", "sale_id"),
        Index("idx_detail_sale_drc_id", "detail_roasted_coffee_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False
    )
    detail_roasted_coffee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("detail_roasted_coffees.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iva_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale = relationship("Sale", back_populates="details")
    detail_roasted_coffee = relationship("DetailRoastedCoffee", back_populates="sale_details")
