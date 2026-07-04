from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.api_v1.auth.dependencies import get_current_user, require_admin
from app.api.api_v1.processes.schema import ProcessCreate, ProcessResponse, ProcessUpdate
from app.api.api_v1.processes.service import ProcessService
from app.core.db.session import get_db



router = APIRouter()


@router.post("/create-bulk", response_model=List[ProcessResponse])
def create_processes_bulk(
    processes: List[ProcessCreate],
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Carga masiva de procesos (modo pruebas).
    Si un proceso falla, los demás continúan.
    """
    service = ProcessService(db)
    created_processes = []

    for process_data in processes:
        try:
            process = service.create_process(process_data)
            created_processes.append(process)
        except Exception as e:
            print(f"Error creando proceso {process_data.invoice_number}: {e}")

    return created_processes


@router.post("/create", response_model=ProcessResponse)
def create_process(
    process: ProcessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Crea un nuevo proceso en el sistema."""
    service = ProcessService(db)
    return service.create_process(process)


@router.get("/get/{process_id}", response_model=ProcessResponse)
def get_process_by_id(
    process_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Obtiene un proceso a partir de su identificador unico."""
    service = ProcessService(db)
    return service.get_process_by_id(process_id)


@router.get("/get", response_model=List[ProcessResponse])
def get_processes(
    search: Optional[str] = Query(None, description="Buscar por numero de factura"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Obtiene la lista de procesos registrados en el sistema."""
    service = ProcessService(db)
    return service.get_processes(search=search)


@router.get("/{process_id}/costs", response_model=dict)
def get_process_costs(
    process_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Desglose completo de costos del proceso: pergamino (regla de 3),
    maquila con IVA, gastos del proceso, y por producto sus costos de
    producción y costo unitario por bolsa (unit_cost).
    """
    from app.api.api_v1.processes.cost_service import ProcessCostService

    return ProcessCostService(db).get_process_costs(process_id)


@router.post("/recalculate-costs", response_model=dict)
def recalculate_costs(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """
    Recalcula el unit_cost de los lotes de TODOS los procesos con los
    valores vigentes (pergamino, maquila, gastos de proceso y de
    producto). Uso principal: backfill de datos históricos tras la
    migración, o rehacer historia si cambia la fórmula.
    """
    from app.api.api_v1.processes.cost_service import ProcessCostService
    from app.models.process import Process

    service = ProcessCostService(db)
    process_ids = [row[0] for row in db.query(Process.id).all()]

    updated_lots = 0
    processed = 0
    for process_id in process_ids:
        updated_lots += service.recalculate_process_costs(process_id)
        processed += 1

    db.commit()
    return {
        "message": "Costos recalculados",
        "processes_processed": processed,
        "lots_updated": updated_lots,
    }


@router.delete("/delete/{process_id}", response_model=dict)
def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Elimina un proceso usando su identificador."""
    service = ProcessService(db)
    if not service.delete_process(process_id):
        raise HTTPException(status_code=404, detail="Process not found")
    return {"message": f"Process {process_id} deleted successfully"}


@router.put("/update/{process_id}", response_model=ProcessResponse)
def update_process(
    process_id: int,
    payload: ProcessUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Actualiza un proceso y reemplaza sus detalles."""
    service = ProcessService(db)
    return service.update_process(process_id, payload)
