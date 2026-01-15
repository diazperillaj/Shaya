from pydantic import BaseModel
from typing import Optional
from app.schemas.person import PersonCreate, PersonResponse

# Modelo para creación (POST)
class UserCreate(BaseModel):
    username: str
    hashed_password: str
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
