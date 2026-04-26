from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

# Ajusta las rutas según la estructura de tu proyecto
from app.api.api_v1.fast_sale.schema import FastSaleCreate, FastSaleResponse, FastSaleUpdate, FastSaleUpdateResponse
from app.api.api_v1.fast_sale.service import FastSaleService
from app.core.db.session import get_db

# from app.api.api_v1.auth.dependencies import get_current_user
# from app.api.api_v1.auth.dependencies import require_admin

from app.core.db.base import Base
from app.core.db.session import engine

router = APIRouter()

@router.post("/create-bulk", response_model=List[FastSaleResponse])
def create_fast_sales_bulk(
    fast_sales: List[FastSaleCreate],
    db: Session = Depends(get_db),
):
    """
    Carga masiva de ventas rápidas (modo pruebas).
    Si una venta falla, las demás continúan.
    """
    service = FastSaleService(db)
    created_fast_sales = []

    for sale_data in fast_sales:
        try:
            sale = service.create_fast_sale(sale_data)
            created_fast_sales.append(sale)
        except Exception as e:
            # logging simple para pruebas
            print(f"Error creando venta rápida: {e}")

    return created_fast_sales


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
    return {"message": "Tables created"}


@router.post("/create", response_model=FastSaleResponse)
def create_fast_sale(
    fast_sale: FastSaleCreate,
    db: Session = Depends(get_db),
    # current_user = Depends(require_admin)
):
    """
    Crea una nueva venta rápida en el sistema.

    Args:
        fast_sale (FastSaleCreate): Datos necesarios para la creación de la venta rápida.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        FastSaleResponse: Venta rápida creada exitosamente.
    Raises:
        HTTPException: Si ocurre un error de validación o de lógica de negocio.
    """
    service = FastSaleService(db)
    return service.create_fast_sale(fast_sale)


@router.put("/update/{fast_sale_id}", response_model=FastSaleUpdateResponse)
def update_fast_sale(
    fast_sale_id: int, 
    fast_sale_data: FastSaleUpdate, 
    db: Session = Depends(get_db),
    # current_user = Depends(require_admin)
):
    """
    Actualiza la información de una venta rápida existente.

    Args:
        fast_sale_id (int): Identificador único de la venta rápida.
        fast_sale_data (FastSaleUpdate): Datos a actualizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        FastSaleUpdateResponse: Venta rápida actualizada.
    Raises:
        HTTPException: Si la venta rápida no existe.
    """
    print(f"Updating Fast Sale {fast_sale_id} with data: {fast_sale_data}")

    service = FastSaleService(db)
    updated_sale = service.update_fast_sale(fast_sale_id, fast_sale_data)
    
    if not updated_sale:
        raise HTTPException(status_code=404, detail="Venta rápida no encontrada")
        
    return updated_sale


@router.get("/get/fast_sale/{fast_sale_id}", response_model=FastSaleResponse)
def get_fast_sale_by_id(
    fast_sale_id: int, 
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)
):
    """
    Obtiene una venta rápida a partir de su identificador único.

    Args:
        fast_sale_id (int): ID de la venta rápida.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        FastSaleResponse: Información de la venta rápida encontrada.

    Raises:
        HTTPException: Si la venta rápida no existe.
    """
    service = FastSaleService(db)
    sale = service.get_fast_sale_by_id(fast_sale_id)
    
    if not sale:
        raise HTTPException(status_code=404, detail="Venta rápida no encontrada")
        
    return sale


@router.get("/get", response_model=List[FastSaleResponse])
def get_fast_sales(
    search: Optional[str] = Query(None, description="Buscar por descripción"),
    db: Session = Depends(get_db),
    # current_user = Depends(get_current_user)
):
    """
    Obtiene una lista de ventas rápidas registradas en el sistema.

    Permite aplicar filtros opcionales mediante parámetros de consulta.

    Args:
        search (str, opcional): Texto para buscar por descripción.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[FastSaleResponse]: Lista de ventas rápidas que cumplen los criterios.
    """
    service = FastSaleService(db)
    if search:
        return service.get_fast_sales_filtered(search=search)
    return service.get_fast_sales()


@router.delete("/delete/{fast_sale_id}", response_model=dict)
def delete_fast_sale(
    fast_sale_id: int, 
    db: Session = Depends(get_db),
    # current_user = Depends(require_admin)
):
    """
    Elimina una venta rápida del sistema usando su identificador.

    Args:
        fast_sale_id (int): ID de la venta rápida a eliminar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        dict: Mensaje de confirmación de eliminación.

    Raises:
        HTTPException: Si la venta rápida no existe.
    """
    service = FastSaleService(db)
    if not service.delete_fast_sale(fast_sale_id):
        raise HTTPException(status_code=404, detail="Venta rápida no encontrada")
        
    return {"message": f"Venta rápida #{fast_sale_id} borrada satisfactoriamente"}