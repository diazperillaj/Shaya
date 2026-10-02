from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func as sql_func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class Employee(Base):
    """
    Trabajador de una finca (modelo-datos §3.9).

    Independiente de `persons`: los recolectores suelen ser informales y no
    deben chocar con sus restricciones únicas (documento, correo). Un
    empleado con historial de pagos se desactiva en lugar de borrarse.
    """

    __tablename__ = "employees"
    __table_args__ = (Index("idx_employee_farm_id", "farm_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farms.id", ondelete="RESTRICT"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    farm = relationship("Farm", back_populates="employees")
