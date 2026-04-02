from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.api_v1.customers.schema import CustomerCreate, CustomerResponse, CustomerUpdate, CustomerUpdateResponse
from app.api.api_v1.customers.service import CustomerService
from app.core.db.session import get_db
from typing import List, Optional

from app.api.api_v1.auth.dependencies import get_current_user
from app.api.api_v1.auth.dependencies import require_admin


from app.models.customer import Customer
from app.models.person import Person


router = APIRouter()


from app.core.db.base import Base
from app.core.db.session import engine



@router.post("/create-bulk", response_model=List[CustomerResponse])
def create_customers_bulk(
    customers: List[CustomerCreate],
    db: Session = Depends(get_db),
):
    """
    Carga masiva de usuarios (modo pruebas).
    Si un usuario falla, los demás continúan.
    """

    service = CustomerService(db)
    created_customers = []

    for customer_data in customers:
        try:
            customer = service.create_customer(customer_data)
            created_customers.append(customer)
        except Exception as e:
            # logging simple para pruebas
            print(f"Error creando usuario {customer_data.person.full_name}: {e}")

    return created_customers






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



@router.post("/create", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Crea un nuevo cliente en el sistema.

    Args:
        customer (CustomerCreate): Datos necesarios para la creación del cliente.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        CustomerResponse: Cliente creado exitosamente.
    Raises:
        HTTPException: Si ocurre un error de validación o de lógica de negocio.
    """
    service = CustomerService(db)
    return service.create_customer(customer)



@router.put("/update/{customer_id}", response_model=CustomerUpdateResponse)
def update_customer(
    customer_id: int, 
    customer_data: CustomerUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Actualiza la información de un cliente existente.

    Args:
        customer_id (int): Identificador único del cliente.
        customer_data (CustomerUpdate): Datos a actualizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        CustomerUpdateResponse: Cliente actualizado.
    Raises:
        HTTPException: Si el cliente no existe.
    """
    service = CustomerService(db)
    return service.update_customer(customer_id, customer_data)



@router.get("/get/customer/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(
    customer_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene un cliente a partir de su identificador único.

    Args:
        customer_id (int): ID del cliente.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        CustomerResponse: Información del cliente encontrado.

    Raises:
        HTTPException: Si el cliente no existe.
    """
    service = CustomerService(db)
    return service.get_customer_by_id(customer_id)



@router.get("/get", response_model=List[CustomerResponse])
def get_customers(
    search: Optional[str] = Query(None, description="Buscar por nombre completo"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)

):
    """
    Obtiene una lista de clientes registrados en el sistema.

    Permite aplicar filtros opcionales mediante parámetros de consulta.

    Args:
        search (str, opcional): Texto para buscar por nombre completo, correo, ciudad, direccion.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[CustomerResponse]: Lista de clientes que cumplen los criterios.
    """
    service = CustomerService(db)
    if search:
        return service.get_customers_filtered(search=search)
    return service.get_customers()



@router.delete("/delete/{customer_id}", response_model=dict)
def delete_customer(
    customer_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Elimina un cliente del sistema usando su identificador.

    Args:
        customer_id (int): ID del cliente a eliminar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        dict: Mensaje de confirmación de eliminación.

    Raises:
        HTTPException: Si el cliente no existe.
    """
    service = CustomerService(db)
    if not service.delete_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": f"Customer {customer_id} deleted successfully"}
