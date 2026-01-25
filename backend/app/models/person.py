from sqlalchemy import Integer, String, Text, DateTime, func as sql_func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base

class Person(Base):
    """
    Modelo ORM que representa la información personal asociada a un usuario.

    Esta entidad almacena los datos personales independientes de las credenciales
    de acceso y mantiene una relación uno a uno con el modelo `User`.
    """
    
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        server_default=sql_func.now()
    )

    user = relationship(
        "User",
        back_populates="person",
        uselist=False,
        cascade="all, delete"
    )
    
    farmer = relationship(
        "Farmer",
        back_populates="person",
        uselist=False,
        cascade="all, delete"
    )
