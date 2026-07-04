import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func as sql_func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base


class FairStatusEnum(enum.Enum):
    open = "open"
    closed = "closed"


class Fair(Base):
    __tablename__ = "fairs"
    __table_args__ = (
        Index("idx_fair_user_id", "user_id"),
        Index("idx_fair_status", "status"),
        Index("idx_fair_start", "start_datetime"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[FairStatusEnum] = mapped_column(
        Enum(FairStatusEnum), nullable=False, default=FairStatusEnum.open
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    sale_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sales.id", ondelete="SET NULL"), nullable=True
    )
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="fairs")
    sale = relationship("Sale", foreign_keys=[sale_id])
    inventory = relationship("FairInventory", back_populates="fair", cascade="all, delete-orphan")
    fair_sales = relationship("FairSale", back_populates="fair", cascade="all, delete-orphan")
    expenses = relationship("FairExpense", back_populates="fair", cascade="all, delete-orphan")
    movements = relationship("InventoryMovement", back_populates="fair", cascade="all, delete-orphan")
