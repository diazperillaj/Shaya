from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.api_v1.farmers.schema import FarmerCreate, FarmerResponse, FarmerUpdate, FarmerUpdateResponse
from app.api.api_v1.farmers.service import FarmerService
from app.core.db.session import get_db
from typing import List, Optional

from app.api.api_v1.auth.dependencies import get_current_user
from app.api.api_v1.auth.dependencies import require_admin


from app.models.farmer import Farmer
from app.models.person import Person


router = APIRouter()


from app.core.db.base import Base
from app.core.db.session import engine



@router.post("/create-bulk", response_model=List[FarmerResponse])
def create_farmers_bulk(
    farmers: List[FarmerCreate],
    db: Session = Depends(get_db),
):
    """
    Carga masiva de usuarios (modo pruebas).
    Si un usuario falla, los demás continúan.
    """

    service = FarmerService(db)
    created_farmers = []

    for farmer_data in farmers:
        try:
            farmer = service.create_farmer(farmer_data)
            created_farmers.append(farmer)
        except Exception as e:
            # logging simple para pruebas
            print(f"Error creando usuario {farmer_data.person.full_name}: {e}")

    return created_farmers




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



@router.post("/create", response_model=FarmerResponse)
def create_farmer(
    farmer: FarmerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Crea un nuevo caficultor en el sistema.

    Args:
        farmer (FarmerCreate): Datos necesarios para la creación del caficultor.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        FarmerResponse: Caficultor creado exitosamente.
    Raises:
        HTTPException: Si ocurre un error de validación o de lógica de negocio.
    """
    service = FarmerService(db)
    return service.create_farmer(farmer)



@router.put("/update/{farmer_id}", response_model=FarmerUpdateResponse)
def update_farmer(
    farmer_id: int, 
    farmer_data: FarmerUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Actualiza la información de un caficultor existente.

    Args:
        farmer_id (int): Identificador único del caficultor.
        farmer_data (FarmerUpdate): Datos a actualizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        FarmerUpdateResponse: Caficultor actualizado.
    Raises:
        HTTPException: Si el caficultor no existe.
    """
    service = FarmerService(db)
    return service.update_farmer(farmer_id, farmer_data)



@router.get("/get/farmer/{farmer_id}", response_model=FarmerResponse)
def get_farmer_by_id(
    farmer_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene un caficultor a partir de su identificador único.

    Args:
        farmer_id (int): ID del caficultor.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        FarmerResponse: Información del caficultor encontrado.

    Raises:
        HTTPException: Si el caficultor no existe.
    """
    service = FarmerService(db)
    return service.get_farmer_by_id(farmer_id)



@router.get("/get", response_model=List[FarmerResponse])
def get_farmers(
    search: Optional[str] = Query(None, description="Buscar por nombre completo"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)

):
    """
    Obtiene una lista de usuarios registrados en el sistema.

    Permite aplicar filtros opcionales mediante parámetros de consulta.

    Args:
        search (str, opcional): Texto para buscar por nombre completo.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[FarmerResponse]: Lista de caficultores que cumplen los criterios.
    """
    service = FarmerService(db)
    if search:
        return service.get_farmers_filtered(search=search)
    return service.get_farmers()



@router.delete("/delete/{farmer_id}", response_model=dict)
def delete_farmer(
    farmer_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Elimina un caficultor del sistema usando su identificador.

    Args:
        farmer_id (int): ID del caficultor a eliminar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        dict: Mensaje de confirmación de eliminación.

    Raises:
        HTTPException: Si el caficultor no existe.
    """
    service = FarmerService(db)
    if not service.delete_farmer(farmer_id):
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {"message": f"Farmer {farmer_id} deleted successfully"}



