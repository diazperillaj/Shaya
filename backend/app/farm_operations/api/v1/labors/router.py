from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.farm_operations.api.v1.dependencies import get_farm_access
from app.farm_operations.api.v1.labors.kinds import LaborKind
from app.farm_operations.api.v1.labors.service import LaborService
from app.farm_operations.services.access import FarmAccess


def build_router(kind: LaborKind) -> APIRouter:
    """
    Rutas de una labor del ciclo: el mismo CRUD para todas
    (especificacion-api §3.5), más `bulk-create` en las que lo admiten.
    """
    router = APIRouter()
    Create, Update, Response, Bulk = (
        kind.create_schema, kind.update_schema, kind.response_schema, kind.bulk_schema,
    )

    def get_service(
        db: Session = Depends(get_db),
        access: FarmAccess = Depends(get_farm_access),
    ) -> LaborService:
        return LaborService(db, access, kind)

    @router.post("/create", response_model=Response, summary=f"{kind.label}: registrar en un lote")
    def create(payload: Create, service: LaborService = Depends(get_service)):
        return service.create(payload)

    if Bulk is not None:
        @router.post(
            "/bulk-create",
            response_model=List[Response],
            summary=f"{kind.label}: registrar en varios lotes",
            description=(
                "Un registro por ciclo, en una sola transacción. Todos los ciclos deben "
                "estar activos y ser de la misma finca."
            ),
        )
        def bulk_create(payload: Bulk, service: LaborService = Depends(get_service)):
            return service.bulk_create(payload)

    @router.get("/get", response_model=List[Response], summary=f"{kind.label}: listar")
    def get_records(
        crop_cycle_id: Optional[int] = Query(None),
        plot_id: Optional[int] = Query(None),
        date_from: Optional[date] = Query(None),
        date_to: Optional[date] = Query(None),
        service: LaborService = Depends(get_service),
    ):
        return service.get_records(
            crop_cycle_id=crop_cycle_id, plot_id=plot_id, date_from=date_from, date_to=date_to,
        )

    @router.put("/update/{record_id}", response_model=Response, summary=f"{kind.label}: corregir")
    def update(record_id: int, payload: Update, service: LaborService = Depends(get_service)):
        return service.update(record_id, payload)

    @router.delete("/delete/{record_id}", response_model=dict, summary=f"{kind.label}: eliminar")
    def delete(record_id: int, service: LaborService = Depends(get_service)):
        service.delete(record_id)
        return {"message": f"Registro {record_id} eliminado exitosamente"}

    return router
