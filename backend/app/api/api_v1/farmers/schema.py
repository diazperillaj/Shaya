from pydantic import BaseModel, StringConstraints
from typing import Optional
from app.schemas.person import PersonCreate, PersonResponse
from typing_extensions import Annotated       
        
        
ValidationLength = Annotated[
    str,
    StringConstraints(min_length=4)
]        

        
class FarmerCreate(BaseModel):
    """
    Modelo utilizado para la creación de caficultores.

    Contiene las validaciones necesarias para garantizar la integridad
    de los datos antes de ser procesados por la lógica de negocio.
    """

    farm_name: ValidationLength
    farm_location: ValidationLength
    person: PersonCreate

class FarmerResponse(BaseModel):
    """
    Modelo de respuesta para endpoints que devuelven información completa
    de un caficultor.
    """

    id: int
    farm_name: str
    farm_location: str
    person: PersonResponse

    class Config:
        orm_mode = True        
        

class FarmerUpdate(BaseModel):
    """
    Modelo utilizado para la actualización parcial de un caficultor.

    Todos los campos son opcionales, permitiendo actualizaciones parciales.
    """

    farm_name: Optional[ValidationLength] = None
    farm_location: Optional[ValidationLength] = None
    person: Optional[PersonCreate] = None

class FarmerUpdateResponse(BaseModel):
    """
    Modelo de respuesta después de una actualización de caficultor.
    """

    id: int
    farm_name: str
    farm_location: str
    person: PersonResponse