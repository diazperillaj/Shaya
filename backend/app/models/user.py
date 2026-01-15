from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=True)

    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"), unique=True)
    person = relationship("Person", back_populates="user")