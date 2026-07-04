import enum
from datetime import datetime
from sqlalchemy import Boolean, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base


class MovementDirectionEnum(enum.Enum):
    """Dirección de una línea de movimiento: entrada suma stock, salida resta."""
    entry = "entry"
    exit = "exit"


class RoastedMovement(Base):
    """Cabecera de un movimiento de salida de inventario de maquilado."""

    __tablename__ = "roasted_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movement_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    details = relationship(
        "RoastedMovementDetail",
        back_populates="movement",
        cascade="all, delete-orphan",
    )


class RoastedMovementDetail(Base):
    """Línea de detalle: un lote específico (DetailRoastedCoffee) y la cantidad descontada."""

    __tablename__ = "roasted_movement_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    movement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roasted_movements.id", ondelete="CASCADE"), nullable=False
    )
    detail_roasted_coffee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("detail_roasted_coffees.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[MovementDirectionEnum] = mapped_column(
        Enum(MovementDirectionEnum),
        nullable=False,
        default=MovementDirectionEnum.exit,
        server_default="exit",
    )
    # True si esta línea CREÓ el lote (entrada de producto nuevo, ej. reempaque).
    # Al eliminar el movimiento, el lote creado se elimina si no tiene usos.
    created_lot: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    movement = relationship("RoastedMovement", back_populates="details")
    detail_roasted_coffee = relationship("DetailRoastedCoffee")
