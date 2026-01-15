from pydantic import BaseModel
from typing import Optional
from app.schemas.person import PersonCreate, PersonResponse

# Modelo para creación (POST)
class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    person: PersonCreate

# Modelo para respuesta (GET / POST response)
class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    person: PersonResponse

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    person: Optional[PersonCreate] = None

class UserUpdateResponse(BaseModel):
    id: int
    username: str
    role: Optional[str]
    person: PersonResponse