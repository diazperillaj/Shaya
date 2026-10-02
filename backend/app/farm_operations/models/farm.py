from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func as sql_func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class Farm(Base):
    """
    Finca gestionada en el módulo de cultivo (modelo-datos §3.1).

    Pertenece siempre a un caficultor existente (`farmers`): primero se crea
    el caficultor y luego sus fincas. La producción propia de Shaya usa el
    caficultor que representa a Shaya. La relación se declara solo desde este
    lado: el núcleo no conoce el módulo de cultivo.
    """

    __tablename__ = "farms"
    __table_args__ = (
        UniqueConstraint("farmer_id", "name", name="uq_farms_farmer_name"),
        Index("idx_farm_farmer_id", "farmer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farmers.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str] = mapped_column(String(255), nullable=False)
    municipality: Mapped[str] = mapped_column(String(255), nullable=False)
    altitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    total_area: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    farmer = relationship("Farmer")
    plots = relationship("Plot", back_populates="farm")
    employees = relationship("Employee", back_populates="farm")
