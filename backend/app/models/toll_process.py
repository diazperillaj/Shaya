# app/models/proceso_maquila.py
from sqlalchemy import Integer, String, Text, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from app.core.db.base import Base
from decimal import Decimal

class TollProcess(Base):
    """
    Modelo ORM que representa el histórico detallado de procesos de maquila.
    
    Registra cada transformación de café pergamino a maquilado,
    incluyendo pesos utilizados, resultados obtenidos y rendimiento del proceso.
    """
    
    __tablename__ = "toll_processes"
    __table_args__ = (
        Index('idx_toll_process_process_date', 'process_date'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    processed_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("processed.id", ondelete="CASCADE"),
        nullable=False
    )
    parchment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parchments.id", ondelete="RESTRICT"),
        nullable=False
    )
    process_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    parchment_weight_used: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    processed_weight_result: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    responsible: Mapped[str] = mapped_column(String(255), nullable=True)
    observations: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relaciones
    processed = relationship("Processed", back_populates="toll_process")
    parchment = relationship("Parchment", back_populates="toll_process")
    
    movements = relationship(
        "InventoryMovement",
        foreign_keys="[InventoryMovement.toll_process_id]",
        back_populates="toll_process",
        cascade="all, delete-orphan"
    )
    
    @hybrid_property
    def rendimiento_porcentaje(self) -> Decimal:
        """Calcula el rendimiento del proceso de maquila en porcentaje"""
        if self.parchment_weight_used > 0:
            return (self.processed_weight_obtained / self.parchment_weight_used) * 100
        return Decimal(0)
