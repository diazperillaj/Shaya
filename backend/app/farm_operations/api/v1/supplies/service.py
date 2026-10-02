from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions.domain import ConflictError, NotFoundError
from app.farm_operations.api.v1.supplies.schema import SupplyCreate, SupplyUpdate
from app.farm_operations.models import Supply
from app.farm_operations.models.enums import SupplyTypeEnum


class SupplyService:
    """
    Catálogo global de insumos, compartido por todas las fincas.

    Cualquier usuario del módulo crea insumos al vuelo desde los formularios
    de labores; desactivar y eliminar queda para el administrador.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_supplies(
        self,
        supply_type: Optional[SupplyTypeEnum] = None,
        search: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> List[Supply]:
        query = self.db.query(Supply)
        if supply_type is not None:
            query = query.filter(Supply.supply_type == supply_type)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(or_(Supply.name.ilike(pattern), Supply.composition.ilike(pattern)))
        if active is not None:
            query = query.filter(Supply.active == active)
        return query.order_by(Supply.name).all()

    def get_supply(self, supply_id: int) -> Supply:
        supply = self.db.query(Supply).filter(Supply.id == supply_id).first()
        if not supply:
            raise NotFoundError("Insumo no encontrado")
        return supply

    def create_supply(self, payload: SupplyCreate) -> Supply:
        self._validate_unique(payload.name, payload.supply_type)
        supply = Supply(**self._fields(payload))
        self.db.add(supply)
        self.db.commit()
        self.db.refresh(supply)
        return supply

    def update_supply(self, supply_id: int, payload: SupplyUpdate) -> Supply:
        supply = self.get_supply(supply_id)
        self._validate_unique(payload.name, payload.supply_type, exclude_id=supply.id)
        for field, value in self._fields(payload).items():
            setattr(supply, field, value)
        self.db.commit()
        self.db.refresh(supply)
        return supply

    def set_active(self, supply_id: int, active: bool) -> Supply:
        supply = self.get_supply(supply_id)
        supply.active = active
        self.db.commit()
        self.db.refresh(supply)
        return supply

    def delete_supply(self, supply_id: int) -> None:
        # Las labores que lo referencien (bloque 2) lo bloquearán con RESTRICT
        supply = self.get_supply(supply_id)
        self.db.delete(supply)
        self.db.commit()

    @staticmethod
    def _fields(payload) -> dict:
        is_other = payload.supply_type == SupplyTypeEnum.other
        return {
            "name": payload.name.strip(),
            "supply_type": payload.supply_type,
            "other_detail": payload.other_detail.strip() if is_other else None,
            "unit": payload.unit.strip(),
            "composition": (payload.composition or "").strip() or None,
        }

    def _validate_unique(self, name: str, supply_type: SupplyTypeEnum, exclude_id: Optional[int] = None) -> None:
        query = self.db.query(Supply.id).filter(
            Supply.supply_type == supply_type, Supply.name.ilike(name.strip())
        )
        if exclude_id is not None:
            query = query.filter(Supply.id != exclude_id)
        if query.first():
            raise ConflictError(f"El insumo «{name.strip()}» ya existe en el catálogo")
