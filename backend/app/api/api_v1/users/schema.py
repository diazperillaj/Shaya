from pydantic import BaseModel, StringConstraints
from typing import Optional
from app.schemas.person import PersonCreate, PersonResponse
from typing_extensions import Annotated

from enum import Enum

class UserRole(str, Enum):
    """
    Enumeración que define los roles permitidos para los usuarios del sistema.
    """
    admin = 'admin'
    user = 'user'


Username = Annotated[
    str,
    StringConstraints(min_length=4)
]

Password = Annotated[
    str,
    StringConstraints(min_length=6)
]

class UserCreate(BaseModel):
    """
    Modelo utilizado para la creación de usuarios.

    Contiene las validaciones necesarias para garantizar la integridad
    de los datos antes de ser procesados por la lógica de negocio.
    """

    username: Username
    password: Password
    role: UserRole
    person: PersonCreate

class UserResponse(BaseModel):
    """
    Modelo de respuesta para endpoints que devuelven información completa
    de un usuario.
    """

    id: int
    username: str
    role: UserRole
    person: PersonResponse

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    """
    Modelo utilizado para la actualización parcial de un usuario.

    Todos los campos son opcionales, permitiendo actualizaciones parciales.
    """

    username: Optional[Username] = None
    password: Optional[Password] = None
    role: Optional[UserRole] = None
    person: Optional[PersonCreate] = None

class UserUpdateResponse(BaseModel):
    """
    Modelo de respuesta después de una actualización de usuario.
    """

    id: int
    username: str
    role: Optional[UserRole]
    person: PersonResponse