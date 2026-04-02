from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.api_v1.users.schema import UserCreate, UserResponse, UserUpdate, UserUpdateResponse
from app.api.api_v1.users.service import UserService
from app.core.db.session import get_db
from typing import List, Optional

from app.api.api_v1.auth.dependencies import get_current_user
from app.api.api_v1.auth.dependencies import require_admin


from app.models.user import User
from app.models.person import Person


router = APIRouter()


from app.core.db.base import Base
from app.core.db.session import engine

@router.get('/create/database/tables')
def create_tables():
    """
    Crea todas las tablas definidas en los modelos de SQLAlchemy.

    ⚠️ ADVERTENCIA:
        Este endpoint está diseñado únicamente para entornos de desarrollo o pruebas.
        No debe exponerse en producción.

    Returns:
        dict: Mensaje de confirmación de creación de tablas.
    """
    Base.metadata.create_all(bind=engine)

    return {"message":"Tables created"}




from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/create-bulk", response_model=List[UserResponse])
def create_users_bulk(
    users: List[UserCreate],
    db: Session = Depends(get_db),
):
    """
    Carga masiva de usuarios (modo pruebas).
    Si un usuario falla, los demás continúan.
    """

    service = UserService(db)
    created_users = []

    for user_data in users:
        try:
            user = service.create_user(user_data)
            created_users.append(user)
        except Exception as e:
            # logging simple para pruebas
            print(f"Error creando usuario {user_data.username}: {e}")

    return created_users




@router.post("/create", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Crea un nuevo usuario en el sistema.

    Args:
        user (UserCreate): Datos necesarios para la creación del usuario.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        UserResponse: Usuario creado exitosamente.

    Raises:
        HTTPException: Si ocurre un error de validación o de lógica de negocio.
    """
    service = UserService(db)
    return service.create_user(user)



@router.put("/update/{user_id}", response_model=UserUpdateResponse)
def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Actualiza la información de un usuario existente.

    Args:
        user_id (int): Identificador único del usuario.
        user_data (UserUpdate): Datos a actualizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        UserUpdateResponse: Usuario actualizado.

    Raises:
        HTTPException: Si el usuario no existe.
    """
    
    service = UserService(db)
    return service.update_user(user_id, user_data)



@router.get("/get/user/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene un usuario a partir de su identificador único.

    Args:
        user_id (int): ID del usuario.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        UserResponse: Información del usuario encontrado.

    Raises:
        HTTPException: Si el usuario no existe.
    """
    service = UserService(db)
    return service.get_user_by_id(user_id)



@router.get("/get", response_model=List[UserResponse])
def get_users(
    search: Optional[str] = Query(None, description="Buscar por username o nombre completo"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)

):
    """
    Obtiene una lista de usuarios registrados en el sistema.

    Permite aplicar filtros opcionales mediante parámetros de consulta.

    Args:
        search (str, opcional): Texto para buscar por usuario o nombre completo.
        role (str, opcional): Rol del usuario.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[UserResponse]: Lista de usuarios que cumplen los criterios.
    """
    service = UserService(db)
    if search or role:
        return service.get_users_filtered(search=search, role=role)
    return service.get_users()



@router.delete("/delete/{user_id}", response_model=dict)
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Elimina un usuario del sistema usando su identificador.

    Args:
        user_id (int): ID del usuario a eliminar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        dict: Mensaje de confirmación de eliminación.

    Raises:
        HTTPException: Si el usuario no existe.
    """
    service = UserService(db)
    if not service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user_id} deleted successfully"}

