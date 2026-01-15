from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=True)

    user = relationship(
        "User",
        back_populates="person",
        uselist=False,
        cascade="all, delete"
    )
