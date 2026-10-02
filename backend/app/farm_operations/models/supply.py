from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    UniqueConstraint,
    func as sql_func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base
from app.farm_operations.models.enums import SupplyTypeEnum


class Supply(Base):
    """
    Insumo agrícola del catálogo global (modelo-datos §3.7).

    Lo comparten todas las fincas: los insumos comerciales son universales.
    Las labores lo referencian por FK; un insumo con historial se desactiva
    en lugar de borrarse.
    """

    __tablename__ = "supplies"
    __table_args__ = (
        UniqueConstraint("name", "supply_type", name="uq_supplies_name_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    supply_type: Mapped[SupplyTypeEnum] = mapped_column(
        Enum(SupplyTypeEnum, name="farmsupplytypeenum"), nullable=False
    )
    other_detail: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    unit: Mapped[str] = mapped_column(
        String(20), nullable=False, default="kg", server_default="kg"
    )
    composition: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )
