from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class FairInventory(Base):
    __tablename__ = "fair_inventories"
    __table_args__ = (
        Index("idx_fair_inv_fair_id", "fair_id"),
        Index("idx_fair_inv_drc_id", "detail_roasted_coffee_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fair_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fairs.id", ondelete="CASCADE"), nullable=False
    )
    detail_roasted_coffee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("detail_roasted_coffees.id", ondelete="RESTRICT"), nullable=False
    )
    initial_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    fair = relationship("Fair", back_populates="inventory")
    detail_roasted_coffee = relationship("DetailRoastedCoffee", back_populates="fair_inventories")
    fair_sales = relationship("FairSale", back_populates="fair_inventory")
