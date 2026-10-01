from pydantic import BaseModel, StringConstraints
from typing import Optional
from app.core.roles import StaffRole, UserRole
from app.schemas.person import PersonCreate, PersonResponse
from typing_extensions import Annotated


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

    Solo admite roles del personal: las cuentas de caficultores se crean
    desde el módulo de cultivo, enlazadas a su registro de caficultor.
    """

    username: Username
    password: Password
    role: StaffRole
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
    El rol solo puede cambiar entre roles del personal.
    """

    username: Optional[Username] = None
    password: Optional[Password] = None
    role: Optional[StaffRole] = None
    person: Optional[PersonCreate] = None

class UserUpdateResponse(BaseModel):
    """
    Modelo de respuesta después de una actualización de usuario.
    """

    id: int
    username: str
    role: Optional[UserRole]
    person: PersonResponse