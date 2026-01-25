from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base

class Farmer(Base):
    """
    Modelo ORM que representa un usuario del sistema.

    Contiene las credenciales de autenticación y autorización,
    y mantiene una relación uno a uno con la entidad `Person`,
    donde se almacenan los datos personales.
    """
    
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    farm_location: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"), unique=True)
    person = relationship("Person", back_populates="farmer")