from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base

class Farmer(Base):
    """
    Modelo ORM que representa un usuario del sistema.

    Contiene la informacion y ubicacion de la finca,
    y mantiene una relación uno a uno con la entidad `Person`,
    donde se almacenan los datos personales.
    """
    
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_name: Mapped[str] = mapped_column(String(255), nullable=False)
    village: Mapped[str] = mapped_column(String(255), nullable=False)
    municipality: Mapped[str] = mapped_column(String(255), nullable=False)

    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"), unique=True)
    person = relationship("Person", back_populates="farmer")
    
    parchments = relationship("Parchment", back_populates="farmer")