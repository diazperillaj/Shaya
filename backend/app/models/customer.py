from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.db.base import Base

class Customer(Base):
    """
    Modelo ORM que representa un cliente del sistema.

    Contiene la informacion del tipo, la direccion y la ciudad del cliente,
    y mantiene una relación uno a uno con la entidad `Person`,
    donde se almacenan los datos personales.
    """
    
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customerType: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)

    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"), unique=True)
    person = relationship("Person", back_populates="customer")
    
    
    
    
    
    
    

