from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserUpdateResponse
from app.services.user_service import UserService
from app.db.session import SessionLocal


import app.models.person
import app.models.user

from app.db.base import Base
from app.db.session import engine


router = APIRouter()

# Dependencia para obtener la sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/create/database/tables')
def create_tables():

    Base.metadata.create_all(bind=engine)

    return {"message":"Tables created"}


@router.post("/create", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(user)

@router.put("/update/{user_id}", response_model=UserUpdateResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.update_user(user_id, user_data)

@router.get("/get/user/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.get_user_by_id(user_id)

@router.get("/get", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.get_users()
