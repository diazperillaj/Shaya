from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.api_v1.products.schema import ProductCreate, ProductResponse, ProductUpdate, ProductUpdateResponse
from app.api.api_v1.products.service import ProductService
from app.core.db.session import get_db
from typing import List, Optional

from app.api.api_v1.auth.dependencies import get_current_user
from app.api.api_v1.auth.dependencies import require_admin


from app.models.product import Product
from app.models.person import Person


router = APIRouter()


from app.core.db.base import Base
from app.core.db.session import engine



@router.post("/create-bulk", response_model=List[ProductResponse])
def create_products_bulk(
    products: List[ProductCreate],
    db: Session = Depends(get_db),
):
    """
    Carga masiva de productos (modo pruebas).
    Si un producto falla, los demás continúan.
    """

    service = ProductService(db)
    created_products = []

    for product_data in products:
        try:
            product = service.create_product(product_data)
            created_products.append(product)
        except Exception as e:
            # logging simple para pruebas
            print(f"Error creando producto {product_data.name}: {e}")

    return created_products




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



@router.post("/create", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    # current_user = Depends(require_admin)
):
    """
    Crea un nuevo caficultor en el sistema.

    Args:
        product (ProductCreate): Datos necesarios para la creación del caficultor.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ProductResponse: Caficultor creado exitosamente.
    Raises:
        HTTPException: Si ocurre un error de validación o de lógica de negocio.
    """
    service = ProductService(db)
    return service.create_product(product)



@router.put("/update/{product_id}", response_model=ProductUpdateResponse)
def update_product(
    product_id: int, 
    product_data: ProductUpdate, 
    db: Session = Depends(get_db),
    # current_user = Depends(require_admin)
):
    """
    Actualiza la información de un caficultor existente.

    Args:
        product_id (int): Identificador único del caficultor.
        product_data (ProductUpdate): Datos a actualizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ProductUpdateResponse: Caficultor actualizado.
    Raises:
        HTTPException: Si el caficultor no existe.
    """
    
    print(f"Updating Product {product_id} with data: {product_data}")

    service = ProductService(db)
    return service.update_product(product_id, product_data)



@router.get("/get/product/{product_id}", response_model=ProductResponse)
def get_product_by_id(
    product_id: int, 
    db: Session = Depends(get_db),
    #Producurrent_user = Depends(get_current_user)ct
):
    """
    Obtiene un caficultor a partir de su identificador único.

    Args:
        product_id (int): ID del caficultor.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ProductResponse: Información del caficultor encontrado.

    Raises:
        HTTPException: Si el caficultor no existe.
    """
    service = ProductService(db)
    return service.get_product_by_id(product_id)



@router.get("/get", response_model=List[ProductResponse])
def get_products(
    search: Optional[str] = Query(None, description="Buscar por nombre completo"),
    db: Session = Depends(get_db),
    #Producurrent_user = Depends(get_current_user)ct

):
    """
    Obtiene una lista de usuarios registrados en el sistema.

    Permite aplicar filtros opcionales mediante parámetros de consulta.

    Args:
        search (str, opcional): Texto para buscar por nombre completo.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[ProductResponse]: Lista de caficultores que cumplen los criterios.
    """
    service = ProductService(db)
    if search:
        return service.get_products_filtered(search=search)
    return service.get_products()



@router.delete("/delete/{product_id}", response_model=dict)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db),
    # current_user = Depends(require_admin)
):
    """
    Elimina un caficultor del sistema usando su identificador.

    Args:
        product_id (int): ID del caficultor a eliminar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        dict: Mensaje de confirmación de eliminación.

    Raises:
        HTTPException: Si el caficultor no existe.
    """
    service = ProductService(db)
    if not service.delete_product(product_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": f"Producto  #{product_id} borrado satisfactoriamente"}



