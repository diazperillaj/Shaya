from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    func as sql_func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class AlertConfig(Base):
    """
    Parámetros de alertas y recordatorios, a nivel de finca o de lote
    (modelo-datos §3.4).

    Cada fila es de una finca o de un lote, nunca de ambos. Un parámetro en
    NULL hereda del nivel superior: lote → finca → valor por defecto del
    sistema (`services/alerts.py`). Las alertas solo notifican; nada de esta
    tabla bloquea una operación.
    """

    __tablename__ = "alert_configs"
    __table_args__ = (
        CheckConstraint(
            "(farm_id IS NULL) != (plot_id IS NULL)",
            name="ck_alert_configs_one_level",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    plot_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("plots.id", ondelete="CASCADE"), nullable=True, unique=True
    )

    fertilization_reminder_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    irrigation_reminder_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phytosanitary_reminder_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weeding_reminder_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    harvest_reminder_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    inactivity_alert_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_drying_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_final_humidity: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    max_final_humidity: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    min_fermentation_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_fermentation_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    broca_alert_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )
