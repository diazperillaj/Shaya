from pydantic import BaseModel, EmailStr
from typing import Optional

class PersonCreate(BaseModel):
    full_name: str
    document: str
    phone: str
    email: EmailStr
    observation: Optional[str] = None

class PersonResponse(PersonCreate):
    id: int

    class Config:
        orm_mode = True
