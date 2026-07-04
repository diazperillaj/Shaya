from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class DetailProcess(Base):
    """
    Modelo ORM para las lineas de detalle de un proceso.
    """

    __tablename__ = "detail_processes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processes.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bag_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    grams_per_bag: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observations: Mapped[str] = mapped_column(Text, nullable=True)

    process = relationship("Process", back_populates="details")
    product = relationship("Product")
