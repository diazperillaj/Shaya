from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.roasted_movements.schema import (
    RoastedMovementCreate,
    RoastedMovementDetailResponse,
    RoastedMovementResponse,
)
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.fair_inventory import FairInventory
from app.models.inventory_movement import InventoryMovement, MovementTypeEnum, ProductMovementTypeEnum
from app.models.product import Product
from app.models.roasted_coffe import RoastedCoffee
from app.models.roasted_movement import MovementDirectionEnum, RoastedMovement, RoastedMovementDetail
from app.models.user import User


class RoastedMovementService:
    def __init__(self, db: Session):
        self.db = db

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_movements(self) -> List[RoastedMovementResponse]:
        movements = (
            self.db.query(RoastedMovement)
            .options(
                joinedload(RoastedMovement.details)
                .joinedload(RoastedMovementDetail.detail_roasted_coffee)
                .joinedload(DetailRoastedCoffee.product)
            )
            .order_by(RoastedMovement.id.desc())
            .all()
        )
        return [self._to_response(m) for m in movements]

    # ── Create ────────────────────────────────────────────────────────────────

    def create_movement(
        self, payload: RoastedMovementCreate, current_user: User
    ) -> RoastedMovementResponse:
        """
        Crea un movimiento de inventario maquilado. Tres modos:

        - Solo salidas: envíos/bajas de lotes existentes (multi-lote).
        - Solo entradas: ajustes positivos a lotes existentes, o lotes
          nuevos (product_id + roasted_coffee_id) con costo manual opcional.
        - Reempaque (salidas + entradas): saca de UN solo lote origen y
          reparte su valor entre las entradas proporcionalmente a los
          gramos por bolsa (conservación de valor). Las entradas quedan
          en el mismo maquilado del lote origen.
        """
        exits = [l for l in payload.details if l.direction == "exit"]
        entries = [l for l in payload.details if l.direction == "entry"]
        is_repack = bool(exits) and bool(entries)

        drc_cache: dict[int, DetailRoastedCoffee] = {}

        def get_drc(drc_id: int) -> DetailRoastedCoffee:
            if drc_id not in drc_cache:
                drc_cache[drc_id] = self._get_drc_or_404(drc_id)
            return drc_cache[drc_id]

        # ── Validaciones de estructura ────────────────────────────────────
        source_drc = None
        if is_repack:
            source_ids = {l.detail_roasted_coffee_id for l in exits}
            if len(source_ids) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un reempaque solo puede sacar de un lote de origen",
                )
            source_drc = get_drc(source_ids.pop())
            for e in entries:
                if not e.grams_per_bag:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Las entradas de un reempaque requieren gramos por bolsa",
                    )
                if e.detail_roasted_coffee_id:
                    target = get_drc(e.detail_roasted_coffee_id)
                    if target.roasted_coffee_id != source_drc.roasted_coffee_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=(
                                "En un reempaque las entradas deben pertenecer "
                                "al mismo maquilado del lote de origen"
                            ),
                        )
        else:
            for e in entries:
                if e.product_id and not e.roasted_coffee_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "Una entrada de producto nuevo requiere el "
                            "maquilado destino (roasted_coffee_id)"
                        ),
                    )

        # Productos y maquilados de lotes nuevos deben existir
        for e in entries:
            if e.product_id:
                self._get_product_or_404(e.product_id)
                if not is_repack:
                    self._get_roasted_coffee_or_404(e.roasted_coffee_id)

        # ── Validación de stock por cambio neto ───────────────────────────
        net_change: dict[int, int] = {}
        for item in payload.details:
            if item.detail_roasted_coffee_id:
                drc = get_drc(item.detail_roasted_coffee_id)
                delta = item.quantity if item.direction == "entry" else -item.quantity
                net_change[drc.id] = net_change.get(drc.id, 0) + delta

        for drc_id, delta in net_change.items():
            drc = drc_cache[drc_id]
            if drc.remaining_quantity + delta < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Stock insuficiente en el lote {drc.id} "
                        f"(producto: {drc.product.name if drc.product else drc.id}). "
                        f"Disponible: {drc.remaining_quantity}, cambio solicitado: {delta}"
                    ),
                )

        # ── Costo de las entradas (conservación de valor en reempaque) ────
        entry_cost: Decimal | None = None
        cost_per_gram: Decimal | None = None
        if is_repack and source_drc.unit_cost is not None:
            value_out = sum(
                (Decimal(l.quantity) * source_drc.unit_cost for l in exits),
                Decimal("0"),
            )
            total_grams_in = sum(e.quantity * e.grams_per_bag for e in entries)
            if total_grams_in > 0:
                cost_per_gram = value_out / Decimal(total_grams_in)

        def cost_for_entry(e) -> Decimal | None:
            if is_repack:
                if cost_per_gram is None:
                    return None
                return (Decimal(e.grams_per_bag) * cost_per_gram).quantize(
                    Decimal("0.01")
                )
            return e.manual_unit_cost

        # ── Aplicar ────────────────────────────────────────────────────────
        try:
            movement = RoastedMovement(
                movement_date=payload.movement_date,
                observations=payload.observations,
                created_by=current_user.id,
            )
            self.db.add(movement)
            self.db.flush()

            for item in payload.details:
                is_entry = item.direction == "entry"
                created_lot = False

                if item.detail_roasted_coffee_id:
                    drc = drc_cache[item.detail_roasted_coffee_id]

                    if is_entry:
                        # Promedio ponderado del costo en reempaques
                        new_cost = cost_for_entry(item)
                        if is_repack and new_cost is not None:
                            if drc.unit_cost is None or drc.remaining_quantity <= 0:
                                drc.unit_cost = new_cost
                            else:
                                drc.unit_cost = (
                                    (
                                        Decimal(drc.remaining_quantity) * drc.unit_cost
                                        + Decimal(item.quantity) * new_cost
                                    )
                                    / Decimal(drc.remaining_quantity + item.quantity)
                                ).quantize(Decimal("0.01"))
                        drc.remaining_quantity += item.quantity
                    else:
                        drc.remaining_quantity -= item.quantity
                else:
                    # Entrada de producto nuevo: crear el lote
                    rc_id = (
                        source_drc.roasted_coffee_id
                        if is_repack
                        else item.roasted_coffee_id
                    )
                    drc = DetailRoastedCoffee(
                        roasted_coffee_id=rc_id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        remaining_quantity=item.quantity,
                        unit_cost=cost_for_entry(item),
                    )
                    self.db.add(drc)
                    self.db.flush()
                    created_lot = True

                self.db.add(RoastedMovementDetail(
                    movement_id=movement.id,
                    detail_roasted_coffee_id=drc.id,
                    quantity=item.quantity,
                    direction=(
                        MovementDirectionEnum.entry if is_entry
                        else MovementDirectionEnum.exit
                    ),
                    created_lot=created_lot,
                ))

                self.db.add(InventoryMovement(
                    movement_date=datetime.now(),
                    movement_type=(
                        MovementTypeEnum.processed_entrance if is_entry
                        else MovementTypeEnum.processed_exit
                    ),
                    product_type=ProductMovementTypeEnum.processed,
                    process_id=drc.roasted_coffee.process_id,
                    quantity=Decimal(item.quantity),
                    reason=(
                        "Movimiento de entrada de maquilado" if is_entry
                        else "Movimiento de salida de maquilado"
                    ),
                    observations=(
                        f"Movimiento #{movement.id} — "
                        f"detail_roasted_coffee_id={drc.id}"
                    ),
                ))

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el movimiento",
            )

        return self._load_or_404(movement.id)

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete_movement(self, movement_id: int) -> bool:
        movement = (
            self.db.query(RoastedMovement)
            .options(
                joinedload(RoastedMovement.details)
                .joinedload(RoastedMovementDetail.detail_roasted_coffee)
            )
            .filter(RoastedMovement.id == movement_id)
            .first()
        )
        if not movement:
            return False

        # Validar reversa antes de tocar datos
        lots_to_delete: list[DetailRoastedCoffee] = []
        for detail in movement.details:
            drc = detail.detail_roasted_coffee
            if not drc:
                continue
            if detail.direction == MovementDirectionEnum.entry:
                if detail.created_lot:
                    self._raise_if_lot_has_other_uses(drc, movement.id)
                    lots_to_delete.append(drc)
                elif drc.remaining_quantity < detail.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"No se puede eliminar el movimiento: el lote "
                            f"{drc.id} ({drc.product.name if drc.product else ''}) "
                            f"solo tiene {drc.remaining_quantity} unidades y la "
                            f"entrada a revertir es de {detail.quantity}. "
                            "Las unidades ya fueron usadas."
                        ),
                    )

        try:
            for detail in movement.details:
                drc = detail.detail_roasted_coffee
                if drc and drc not in lots_to_delete:
                    if detail.direction == MovementDirectionEnum.entry:
                        drc.remaining_quantity -= detail.quantity
                    else:
                        drc.remaining_quantity += detail.quantity

            self.db.delete(movement)
            self.db.flush()

            # Los lotes creados por este movimiento se eliminan con él
            for drc in lots_to_delete:
                self.db.delete(drc)

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el movimiento",
            )

        return True

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_or_404(self, movement_id: int) -> RoastedMovementResponse:
        movement = (
            self.db.query(RoastedMovement)
            .options(
                joinedload(RoastedMovement.details)
                .joinedload(RoastedMovementDetail.detail_roasted_coffee)
                .joinedload(DetailRoastedCoffee.product)
            )
            .filter(RoastedMovement.id == movement_id)
            .first()
        )
        if not movement:
            raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        return self._to_response(movement)

    def _get_product_or_404(self, product_id: int) -> Product:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Producto con id={product_id} no encontrado",
            )
        return product

    def _get_roasted_coffee_or_404(self, roasted_coffee_id: int) -> RoastedCoffee:
        rc = (
            self.db.query(RoastedCoffee)
            .filter(RoastedCoffee.id == roasted_coffee_id)
            .first()
        )
        if not rc:
            raise HTTPException(
                status_code=404,
                detail=f"Maquilado con id={roasted_coffee_id} no encontrado",
            )
        return rc

    def _raise_if_lot_has_other_uses(
        self, drc: DetailRoastedCoffee, movement_id: int
    ) -> None:
        """
        Lanza 409 si un lote creado por el movimiento ya tiene usos
        (ventas, ferias u otros movimientos): hay que borrarlos primero.
        """
        relations: list[str] = []

        sale_count = (
            self.db.query(DetailSale)
            .filter(DetailSale.detail_roasted_coffee_id == drc.id)
            .count()
        )
        if sale_count:
            relations.append(f"{sale_count} venta(s)")

        fair_count = (
            self.db.query(FairInventory)
            .filter(FairInventory.detail_roasted_coffee_id == drc.id)
            .count()
        )
        if fair_count:
            relations.append(f"{fair_count} inventario(s) de feria")

        other_movements = (
            self.db.query(RoastedMovementDetail)
            .filter(
                RoastedMovementDetail.detail_roasted_coffee_id == drc.id,
                RoastedMovementDetail.movement_id != movement_id,
            )
            .count()
        )
        if other_movements:
            relations.append(f"{other_movements} línea(s) de otros movimientos")

        if relations:
            product_name = drc.product.name if drc.product else f"#{drc.id}"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"No se puede eliminar el movimiento: el lote de "
                    f"'{product_name}' que creó ya está relacionado con "
                    f"{'; '.join(relations)}. Elimina primero esos registros."
                ),
            )

    def _get_drc_or_404(self, drc_id: int) -> DetailRoastedCoffee:
        drc = (
            self.db.query(DetailRoastedCoffee)
            .options(
                joinedload(DetailRoastedCoffee.roasted_coffee),
                joinedload(DetailRoastedCoffee.product),
            )
            .filter(DetailRoastedCoffee.id == drc_id)
            .first()
        )
        if not drc:
            raise HTTPException(
                status_code=404,
                detail=f"Lote de maquilado con id={drc_id} no encontrado",
            )
        return drc

    @staticmethod
    def _to_response(m: RoastedMovement) -> RoastedMovementResponse:
        return RoastedMovementResponse(
            id=m.id,
            movement_date=m.movement_date,
            observations=m.observations,
            created_by=m.created_by,
            details=[
                RoastedMovementDetailResponse(
                    id=d.id,
                    detail_roasted_coffee_id=d.detail_roasted_coffee_id,
                    roasted_coffee_id=(
                        d.detail_roasted_coffee.roasted_coffee_id
                        if d.detail_roasted_coffee else 0
                    ),
                    product_name=(
                        d.detail_roasted_coffee.product.name
                        if d.detail_roasted_coffee and d.detail_roasted_coffee.product
                        else ""
                    ),
                    quantity=d.quantity,
                    direction=d.direction.value if d.direction else "exit",
                    created_lot=bool(d.created_lot),
                )
                for d in m.details
            ],
        )
