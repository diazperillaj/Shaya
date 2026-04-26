from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.parchment import Parchment as ParchmentCreate

from app.api.api_v1.inventory.schema import (
    ParchmentCreate,
    ParchmentResponse,
    ParchmentUpdate,
    ParchmentUpdateResponse,
    ParchmentDetailResponse,
    ParchmentInventoryAdjustment,
    ParchmentAdjustmentResponse,
    ParchmentMovementHistory,
    ParchmentInventorySummary
)
from app.api.api_v1.inventory.service import ParchmentService
from app.core.db.session import get_db
from typing import List, Optional
from decimal import Decimal

from app.api.api_v1.auth.dependencies import get_current_user
from app.api.api_v1.auth.dependencies import require_admin

router = APIRouter()



# ============================================================================
# PARCHMENT ENDPOINTS
# ============================================================================

@router.post("/create-bulk", response_model=List[ParchmentResponse])
def create_parchments_bulk(
    parchments: List[ParchmentCreate],
    db: Session = Depends(get_db),
):
    """
    Carga masiva de productos (modo pruebas).
    Si un producto falla, los demás continúan.
    """

    service = ParchmentService(db)
    created_parchments = []

    for parchment_data in parchments:
        try:
            parchment = service.create_parchment(parchment_data)
            created_parchments.append(parchment)
        except Exception as e:
            # logging simple para pruebas
            print(f"Error creando pergamino {parchment_data.name}: {e}")

    return created_parchments

@router.post("/create", response_model=ParchmentResponse, tags=["Parchments"])
def create_parchment(
    parchment: ParchmentCreate,
    db: Session = Depends(get_db),
):
    """
    Crea un nuevo registro de café pergamino en el inventario.

    Este endpoint:
    - Registra la compra de café pergamino
    - Crea el inventario base
    - Genera automáticamente el movimiento de entrada

    Args:
        parchment (ParchmentCreate): Datos necesarios para la creación del pergamino.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ParchmentResponse: Pergamino creado exitosamente.
        
    Raises:
        HTTPException: Si ocurre un error de validación o de lógica de negocio.
    """
    service = ParchmentService(db)
    return service.create_parchment(parchment)


@router.put("/update/{parchment_id}", response_model=ParchmentUpdateResponse, tags=["Parchments"])
def update_parchment(
    parchment_id: int,
    parchment_data: ParchmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """
    Actualiza la información descriptiva de un pergamino existente.

    Nota: Las cantidades NO se actualizan aquí, solo mediante movimientos de inventario.

    Args:
        parchment_id (int): Identificador único del pergamino.
        parchment_data (ParchmentUpdate): Datos a actualizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ParchmentUpdateResponse: Pergamino actualizado.
        
    Raises:
        HTTPException: Si el pergamino no existe.
    """    
    service = ParchmentService(db)
    return service.update_parchment(parchment_id, parchment_data)


@router.get("/get/{parchment_id}", response_model=ParchmentDetailResponse, tags=["Parchments"])
def get_parchment_by_id(
    parchment_id: int,
    db: Session = Depends(get_db),
    # current_user=Depends(get_current_user)
):
    """
    Obtiene un pergamino a partir de su identificador único.

    Incluye información detallada del caficultor y cálculos derivados.

    Args:
        parchment_id (int): ID del pergamino.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ParchmentDetailResponse: Información completa del pergamino encontrado.

    Raises:
        HTTPException: Si el pergamino no existe.
    """
    service = ParchmentService(db)
    parchment = service.get_parchment_by_id(parchment_id)
    
    # Calcular valores derivados
    used_quantity = parchment.initial_quantity - parchment.remaining_quantity
    used_percentage = (used_quantity / parchment.initial_quantity * 100) if parchment.initial_quantity > 0 else Decimal(0)
    
    return {
        **parchment.__dict__,
        "farmer": parchment.farmer,
        "used_quantity": used_quantity,
        "used_percentage": used_percentage,
        "remaining_inventory_value": parchment.remaining_quantity * parchment.purchase_price,
        "total_purchase_value": parchment.initial_quantity * parchment.purchase_price
    }


@router.get("/get", response_model=List[ParchmentResponse], tags=["Parchments"])
def get_parchments(
    search: Optional[str] = Query(None, description="Buscar por caficultor, variedad o lote"),
    farmer_id: Optional[int] = Query(None, description="Filtrar por ID de caficultor"),
    variety: Optional[str] = Query(None, description="Filtrar por variedad de café"),
    min_quantity: Optional[Decimal] = Query(None, description="Cantidad mínima disponible"),
    db: Session = Depends(get_db),
    # current_user=Depends(get_current_user)
):
    """
    Obtiene una lista de pergaminos registrados en el sistema.

    Permite aplicar filtros opcionales mediante parámetros de consulta.

    Args:
        search (str, opcional): Texto para buscar por caficultor, variedad o lote.
        farmer_id (int, opcional): Filtrar por caficultor específico.
        variety (str, opcional): Filtrar por variedad de café.
        min_quantity (Decimal, opcional): Filtrar por cantidad mínima disponible.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[ParchmentResponse]: Lista de pergaminos que cumplen los criterios.
    """
    service = ParchmentService(db)
    
    if search or farmer_id or variety or min_quantity:
        return service.get_parchments_filtered(
            search=search,
            farmer_id=farmer_id,
            variety=variety,
            min_quantity=min_quantity
        )
    
    return service.get_parchments()


@router.delete("/delete/{parchment_id}", response_model=dict, tags=["Parchments"])
def delete_parchment(
    parchment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """
    Elimina un pergamino del sistema usando su identificador.

    Nota: No se puede eliminar si tiene productos maquilados derivados.

    Args:
        parchment_id (int): ID del pergamino a eliminar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        dict: Mensaje de confirmación de eliminación.

    Raises:
        HTTPException: Si el pergamino no existe o tiene productos derivados.
    """
    service = ParchmentService(db)
    if not service.delete_parchment(parchment_id):
        raise HTTPException(status_code=404, detail="Parchment not found")
    return {"message": f"Parchment {parchment_id} deleted successfully"}


@router.post("/adjust-inventory", response_model=ParchmentAdjustmentResponse, tags=["Parchments"])
def adjust_parchment_inventory(
    adjustment: ParchmentInventoryAdjustment,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """
    Realiza un ajuste manual de inventario de pergamino.

    Permite realizar:
    - Ajustes (correcciones de inventario)
    - Mermas (pérdidas por daño, humedad, etc.)
    - Devoluciones (entradas por devolución)

    Args:
        adjustment (ParchmentInventoryAdjustment): Datos del ajuste a realizar.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ParchmentAdjustmentResponse: Información del ajuste realizado.

    Raises:
        HTTPException: Si el pergamino no existe o cantidad insuficiente.
    """
    service = ParchmentService(db)
    return service.adjust_parchment_inventory(adjustment)


@router.get("/movement-history/{parchment_id}", response_model=ParchmentMovementHistory, tags=["Parchments"])
def get_parchment_movement_history(
    parchment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Obtiene el historial completo de movimientos de un pergamino.

    Permite ver la trazabilidad completa:
    - Entrada inicial (compra)
    - Salidas para maquila
    - Ventas directas
    - Ajustes y mermas

    Args:
        parchment_id (int): ID del pergamino.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ParchmentMovementHistory: Información del pergamino y su historial de movimientos.

    Raises:
        HTTPException: Si el pergamino no existe.
    """
    service = ParchmentService(db)
    return service.get_parchment_movement_history(parchment_id)


@router.get("/inventory-summary", response_model=ParchmentInventorySummary, tags=["Parchments"])
def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Obtiene un resumen general del inventario de café pergamino.

    Incluye:
    - Total de pergaminos registrados
    - Total de kg disponibles
    - Total de kg usados
    - Valor total del inventario
    - Precio promedio de compra

    Args:
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        ParchmentInventorySummary: Resumen estadístico del inventario.
    """
    service = ParchmentService(db)
    return service.get_inventory_summary()


@router.post("/create-bulk", response_model=List[ParchmentResponse], tags=["Parchments"])
def create_parchments_bulk(
    parchments: List[ParchmentCreate],
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """
    Carga masiva de pergaminos (modo pruebas/migración).
    
    Si un pergamino falla, los demás continúan.

    Args:
        parchments (List[ParchmentCreate]): Lista de pergaminos a crear.
        db (Session): Sesión de base de datos (dependencia).

    Returns:
        List[ParchmentResponse]: Pergaminos creados exitosamente.
    """
    service = ParchmentService(db)
    created_parchments = []

    for parchment_data in parchments:
        try:
            parchment = service.create_parchment(parchment_data)
            created_parchments.append(parchment)
        except Exception as e:
            # Logging simple para pruebas
            print(f"Error creating parchment for farmer {parchment_data.farmer_id}: {e}")

    return created_parchments
