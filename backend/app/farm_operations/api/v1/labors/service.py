from datetime import date
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.core.exceptions.domain import ConflictError, NotFoundError
from app.farm_operations.api.v1.labors.kinds import LaborKind
from app.farm_operations.models import CropCycle, Plot, Supply
from app.farm_operations.models.enums import CycleStatusEnum, PlotStatusEnum
from app.farm_operations.services.access import FarmAccess
from app.farm_operations.services.dates import format_date


class LaborService:
    """
    Registro de una labor del ciclo, dentro del alcance del usuario.

    Reglas comunes a todas las labores:
    - la fecha cae dentro del ciclo (desde su inicio y, si está cerrado,
      hasta su fin): así un registro olvidado se completa después del cierre
      sin romper la línea de tiempo del lote;
    - un lote cerrado no recibe labores nuevas;
    - un insumo desactivado no se usa en registros nuevos.
    """

    def __init__(self, db: Session, access: FarmAccess, kind: LaborKind):
        self.db = db
        self.access = access
        self.kind = kind
        self.model = kind.model

    # ── Consultas ─────────────────────────────────────────────────────────

    def get_records(
        self,
        crop_cycle_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[dict]:
        date_column = self.kind.date_column
        query = self.access.cycle_records(self.model).options(
            contains_eager(self.model.crop_cycle).contains_eager(CropCycle.plot)
        )
        if self._has_supply:
            query = query.options(joinedload(self.model.supply))
        if crop_cycle_id is not None:
            query = query.filter(self.model.crop_cycle_id == crop_cycle_id)
        if plot_id is not None:
            query = query.filter(CropCycle.plot_id == plot_id)
        if date_from is not None:
            query = query.filter(date_column >= date_from)
        if date_to is not None:
            query = query.filter(date_column <= date_to)

        records = query.order_by(date_column.desc(), self.model.id.desc()).all()
        return [self._to_response(record) for record in records]

    # ── Escritura ─────────────────────────────────────────────────────────

    def create(self, payload: BaseModel) -> dict:
        cycle = self.access.get_cycle(payload.crop_cycle_id)
        data = self.kind.normalize(payload.model_dump(exclude={"crop_cycle_id"}))
        self._validate(cycle, data)

        record = self.model(crop_cycle_id=cycle.id, **data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def bulk_create(self, payload: BaseModel) -> List[dict]:
        """
        La misma labor en varios lotes de una finca, en una sola transacción.

        Se guarda un registro por ciclo — el análisis necesita la labor
        atribuida a cada lote —, con los montos de cada uno.
        """
        shared = payload.model_dump(exclude={"items"})
        cycles = [self.access.get_cycle(item.crop_cycle_id) for item in payload.items]

        if len({cycle.plot.farm_id for cycle in cycles}) > 1:
            raise ConflictError("Todos los lotes deben ser de la misma finca")
        for cycle in cycles:
            if cycle.status != CycleStatusEnum.active:
                raise ConflictError(
                    f"El lote «{cycle.plot.name}» no tiene el ciclo activo: regístralo por separado"
                )

        records = []
        for cycle, item in zip(cycles, payload.items):
            data = self.kind.normalize({**shared, **item.model_dump(exclude={"crop_cycle_id"})})
            self._validate(cycle, data)
            records.append(self.model(crop_cycle_id=cycle.id, **data))

        # Todo o nada: si una validación falla, no se agregó ningún registro
        self.db.add_all(records)
        self.db.commit()
        for record in records:
            self.db.refresh(record)
        return [self._to_response(record) for record in records]

    def update(self, record_id: int, payload: BaseModel) -> dict:
        record = self._get(record_id)
        data = self.kind.normalize(payload.model_dump())
        self._validate(record.crop_cycle, data, current=record)

        for field, value in data.items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return self._to_response(record)

    def delete(self, record_id: int) -> None:
        record = self._get(record_id)
        self.db.delete(record)
        self.db.commit()

    # ── Internos ──────────────────────────────────────────────────────────

    @property
    def _has_supply(self) -> bool:
        return hasattr(self.model, "supply_id")

    def _get(self, record_id: int):
        record = self.access.cycle_records(self.model).filter(self.model.id == record_id).first()
        if not record:
            raise NotFoundError("Registro no encontrado")
        return record

    def _validate(self, cycle: CropCycle, data: dict, current=None) -> None:
        plot: Plot = cycle.plot
        if current is None and plot.status == PlotStatusEnum.closed:
            raise ConflictError(f"El lote «{plot.name}» está cerrado: no admite labores nuevas")

        record_date: date = data[self.kind.date_field]
        if record_date < cycle.start_date:
            raise ConflictError(
                f"La fecha es anterior al inicio del ciclo {cycle.cycle_number} del lote "
                f"«{plot.name}» ({format_date(cycle.start_date)})"
            )
        if cycle.end_date is not None and record_date > cycle.end_date:
            raise ConflictError(
                f"La fecha es posterior al cierre del ciclo {cycle.cycle_number} del lote "
                f"«{plot.name}» ({format_date(cycle.end_date)})"
            )

        if self._has_supply:
            self._validate_supply(data["supply_id"], current)

    def _validate_supply(self, supply_id: int, current) -> None:
        supply = self.db.get(Supply, supply_id)
        if supply is None:
            raise NotFoundError("Insumo no encontrado")
        keeps_same = current is not None and current.supply_id == supply_id
        if not supply.active and not keeps_same:
            raise ConflictError(f"El insumo «{supply.name}» está desactivado")

    def _to_response(self, record) -> dict:
        data = {column.key: getattr(record, column.key) for column in self.model.__table__.columns}
        cycle = record.crop_cycle
        data.update(
            cycle_number=cycle.cycle_number,
            plot_id=cycle.plot_id,
            plot_name=cycle.plot.name,
        )
        if self._has_supply:
            supply = record.supply
            data["supply"] = {"id": supply.id, "name": supply.name, "unit": supply.unit}
        return data
