import enum
from typing import Optional
from typing_extensions import Annotated
from pydantic import BaseModel, StringConstraints, ConfigDict, field_validator

# Se asume que estos modelos están definidos correctamente en su respectivo archivo
from app.schemas.person import PersonCreate, PersonResponse

ValidationLength = Annotated[
    str,
    StringConstraints(min_length=4)
]        

# Heredar de `str` asegura que Pydantic y FastAPI serialicen correctamente el Enum a JSON
class ProductTypeEnum(str, enum.Enum):
    """Enumeración para tipos de producto"""
    parchment = "parchment"
    processed = "processed"
    other = "other"
        
class ProductCreate(BaseModel):
    """
    Modelo utilizado para la creación de productos.

    Contiene las validaciones necesarias para garantizar la integridad
    de los datos antes de ser procesados por la lógica de negocio.
    """
    name: ValidationLength
    quantity: int
    type: ProductTypeEnum
    description: Optional[str] = None
    
    @field_validator("description", mode="before")
    def empty_to_none(cls, v):
        if v == "":
            return None
        return v

class ProductResponse(BaseModel):
    """
    Modelo de respuesta para endpoints que devuelven información completa
    de un producto.
    """
    id: int
    name: str
    quantity: int
    type: ProductTypeEnum
    description: Optional[str] = None

    # En Pydantic V2, `Config: orm_mode = True` se reemplaza por `model_config`
    model_config = ConfigDict(from_attributes=True)
        
class ProductUpdate(BaseModel):
    """
    Modelo utilizado para la actualización parcial de un producto.

    Todos los campos son opcionales, permitiendo actualizaciones parciales.
    """
    name: Optional[ValidationLength] = None
    quantity: Optional[int] = None
    type: Optional[ProductTypeEnum] = None
    description: Optional[str] = None
    
    @field_validator("description", mode="before")
    def empty_to_none(cls, v):
        if v == "":
            return None
        return v

class ProductUpdateResponse(BaseModel):
    """
    Modelo de respuesta después de una actualización de producto.
    """
    id: int
    name: str
    quantity: int
    type: ProductTypeEnum
    description: Optional[str] = None
