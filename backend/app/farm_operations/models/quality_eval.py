from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func as sql_func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base
from app.farm_operations.models.enums import QualityStageEnum

PERCENT_COLUMNS = ("ripe_pct", "green_pct", "overripe_pct", "bored_pct", "humidity_pct", "defects_pct", "score")


class QualityEval(Base):
    """
    Evaluación de calidad (modelo-datos §3.13): en cereza, de una cosecha; en
    pergamino, de un secado. Una sola tabla con la etapa (decisión D5).
    """

    __tablename__ = "quality_evals"
    __table_args__ = (
        CheckConstraint(
            "(stage = 'cherry' AND harvest_id IS NOT NULL AND drying_id IS NULL)"
            " OR (stage = 'parchment' AND drying_id IS NOT NULL AND harvest_id IS NULL)",
            name="ck_quality_evals_stage_ref",
        ),
        CheckConstraint(
            " AND ".join(f"({column} IS NULL OR ({column} >= 0 AND {column} <= 100))" for column in PERCENT_COLUMNS),
            name="ck_quality_evals_ranges",
        ),
        Index("idx_quality_eval_harvest_id", "harvest_id"),
        Index("idx_quality_eval_drying_id", "drying_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stage: Mapped[QualityStageEnum] = mapped_column(
        Enum(QualityStageEnum, name="farmqualitystageenum"), nullable=False
    )
    harvest_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("harvests.id", ondelete="RESTRICT"), nullable=True
    )
    drying_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("dryings.id", ondelete="RESTRICT"), nullable=True
    )
    eval_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Etapa cereza
    ripe_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    green_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    overripe_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    bored_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    # Etapa pergamino
    humidity_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    defects_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    yield_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    harvest = relationship("Harvest")
    drying = relationship("Drying")
