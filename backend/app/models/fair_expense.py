import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, func as sql_func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class ExpenseCategoryEnum(enum.Enum):
    food = "food"
    supplies = "supplies"
    transport = "transport"
    other = "other"


class FairExpense(Base):
    __tablename__ = "fair_expenses"
    __table_args__ = (
        Index("idx_fair_exp_fair_id", "fair_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fair_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fairs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[ExpenseCategoryEnum] = mapped_column(Enum(ExpenseCategoryEnum), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_func.now()
    )

    fair = relationship("Fair", back_populates="expenses")
    user = relationship("User", back_populates="fair_expenses")
