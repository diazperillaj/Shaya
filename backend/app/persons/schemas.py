from pydantic import BaseModel

class PersonCreate(BaseModel):
    full_name: str
    document: str
    phone: str
    email: str
    observation: str

class PersonResponse(PersonCreate):
    id: int
