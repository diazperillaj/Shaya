from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserUpdateResponse
from app.services.user_service import UserService
from app.db.session import SessionLocal
from typing import List, Optional



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


@router.get("/filter", response_model=List[UserResponse])
def list_users(
    search: Optional[str] = Query(None, description="Buscar por username o nombre completo"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    return service.get_users_filtered(search=search, role=role)

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

@router.get("/get", response_model=List[UserResponse])
def get_users(
    search: Optional[str] = Query(None, description="Buscar por username o nombre completo"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    db: Session = Depends(get_db)
):
    service = UserService(db)
    if search or role:
        return service.get_users_filtered(search=search, role=role)
    return service.get_users()

@router.delete("/delete/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    if not service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user_id} deleted successfully"}

