from pydantic import BaseModel, StringConstraints
from typing import Optional
from app.schemas.person import PersonCreate, PersonResponse
from typing_extensions import Annotated       
        
ValidationLength = Annotated[
    str,
    StringConstraints(min_length=2),
]        

        
class CustomerCreate(BaseModel):
    """
    Modelo utilizado para la creación de clientes.

    Contiene las validaciones necesarias para garantizar la integridad
    de los datos antes de ser procesados por la lógica de negocio.
    """

    customerType: ValidationLength
    address: ValidationLength
    city: ValidationLength
    person: PersonCreate

class CustomerResponse(BaseModel):
    """
    Modelo de respuesta para endpoints que devuelven información completa
    de un cliente.
    """

    id: int
    customerType: str
    address: str
    city: str
    person: PersonResponse

    class Config:
        orm_mode = True        
        

class CustomerUpdate(BaseModel):
    """
    Modelo utilizado para la actualización parcial de un cliente.

    Todos los campos son opcionales, permitiendo actualizaciones parciales.
    """

    customerType: Optional[ValidationLength] = None
    address: Optional[ValidationLength] = None
    city: Optional[ValidationLength] = None
    person: Optional[PersonCreate] = None

class CustomerUpdateResponse(BaseModel):
    """
    Modelo de respuesta después de una actualización de caficultor.
    """

    id: int
    customerType: str
    address: str
    city: str
    person: PersonResponse