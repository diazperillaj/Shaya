from fastapi import APIRouter, Depends, Response, HTTPException
from datetime import timedelta
from sqlalchemy.orm import Session

from app.api.api_v1.auth.schema import LoginSchema, UserResponse
from app.api.api_v1.auth.service import authenticate_user
from app.api.api_v1.auth.dependencies import get_current_user
from app.core.security import create_access_token
from app.core.db.session import get_db



router = APIRouter()

from app.api.api_v1.users.router import create_tables
from app.models.person import Person
from app.models.user import User
from app.core.db.session import engine
from app.core.security import get_password_hash

@router.get('/create/database/tables')
def createTablesOnAuth():
    return create_tables()


@router.get('/insert/user')
def insertUserOnAuth():
    
    person = Person(
        full_name="Juan Pablo Diaz",
        document="12345678",
        phone="555-1234",
        email="diazperillaj@gmail.com",
        observation="Usuario administrador por defecto"
    )
    
    user = User(
        username='admin',
        hashed_password= get_password_hash('admin1'),
        role='admin',
        person=person
    )
    
    session = Session(bind=engine)
    session.add(user)
    session.commit()
    session.close()
    
    return {"message":"Admin user created"}
    
    
    

@router.post("/login")
def login(
    data: LoginSchema,
    response: Response,
    db: Session = Depends(get_db)
):

    user = authenticate_user(db, data.username, data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")


    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=8)
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,      # HTTP local
        samesite="lax",    # 🔥 CLAVE
        max_age=60 * 60 * 8
    )

    return {"message": f"Login exitoso"}


@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logout exitoso"}
