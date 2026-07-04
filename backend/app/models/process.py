from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class Process(Base):
    """
    Modelo ORM para el encabezado del proceso de maquila.

    Este modelo representa el registro principal que consume el frontend
    en la vista de procesos. Los detalles se manejaran en un modelo aparte.
    """

    __tablename__ = "processes"
    __table_args__ = (
        Index("idx_process_invoice_number", "invoice_number"),
        Index("idx_process_process_date", "process_date"),
        Index("idx_process_parchment_id", "parchment_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    process_date: Mapped[date] = mapped_column(Date, nullable=False)
    parchment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parchments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    parchment_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    resultant_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    yield_percentage: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    iva: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observations: Mapped[str] = mapped_column(Text, nullable=True)

    # Relacion con inventario de pergamino seco usado por el proceso
    parchment = relationship("Parchment", back_populates="processes")
    details = relationship(
        "DetailProcess",
        back_populates="process",
        cascade="all, delete-orphan",
    )
    
    roasted_coffees = relationship(
        "RoastedCoffee",
        back_populates="process",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    movements = relationship(
        "InventoryMovement",
        back_populates="process",
        cascade="all, delete-orphan"
    )

    # Sin cascade de borrado: los gastos bloquean la eliminación del
    # proceso (FK RESTRICT) y deben borrarse manualmente primero.
    expenses = relationship("ProcessExpense", back_populates="process")
