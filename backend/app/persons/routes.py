from fastapi import APIRouter
from app.persons.schemas import PersonCreate
from app.persons.service import create_person

router = APIRouter(prefix="/persons", tags=["Persons"])

@router.post("/")
def create_person_endpoint(person: PersonCreate):
    create_person(person.model_dump())
    return {"message": "Person created"}
