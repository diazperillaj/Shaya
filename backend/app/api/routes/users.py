from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.db.session import SessionLocal

router = APIRouter()

# Dependencia para obtener la sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create/user", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(user)

@router.get("/get/user/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.get_user_by_id(user_id)

@router.get("/get/users", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.get_users()
