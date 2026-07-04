from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import cast, desc, or_, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.roasted_coffee.schema import (
    DetailRoastedCoffeeCreate,
    DetailRoastedCoffeeUpdate,
    RoastedCoffeeCreate,
    RoastedCoffeeDeleteResponse,
    RoastedCoffeeInventoryResponse,
    RoastedCoffeeProductResponse,
    RoastedCoffeeUpdate,
)
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.inventory_movement import InventoryMovement, MovementTypeEnum, ProductMovementTypeEnum
from app.models.parchment import Parchment
from app.models.process import Process
from app.models.product import Product
from app.models.roasted_coffe import RoastedCoffee


class RoastedCoffeeService:
    """Servicio de negocio para el inventario de café maquilado."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Queries públicas
    # ------------------------------------------------------------------

    def get_roasted_coffees(
        self, search: Optional[str] = None
    ) -> List[RoastedCoffeeInventoryResponse]:
        query = self._base_query()

        if search:
            query = query.filter(
                or_(
                    cast(RoastedCoffee.id, String).ilike(f"%{search}%"),
                    cast(RoastedCoffee.process_id, String).ilike(f"%{search}%"),
                    Parchment.variety.ilike(f"%{search}%"),
                    Product.name.ilike(f"%{search}%"),
                )
            )

        roasted_coffees = query.order_by(desc(RoastedCoffee.id)).distinct().all()
        return [self._to_response(r) for r in roasted_coffees]

    def get_roasted_coffee_by_id(
        self, roasted_coffee_id: int
    ) -> RoastedCoffeeInventoryResponse:
        roasted = (
            self._base_query()
            .filter(RoastedCoffee.id == roasted_coffee_id)
            .first()
        )
        if not roasted:
            raise HTTPException(status_code=404, detail="Maquilado no encontrado")
        return self._to_response(roasted)

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------

    def create_roasted_coffee(
        self, payload: RoastedCoffeeCreate
    ) -> RoastedCoffeeInventoryResponse:
        """
        Crea un maquilado manualmente con commit propio.
        Para uso interno desde ProcessService usar build_roasted_coffee_in_transaction.
        """
        try:
            self._check_duplicate_process(payload.process_id)
            roasted = self._build_roasted_coffee(
                process_id=payload.process_id,
                observations=payload.observations,
                details=payload.details,
            )
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear el maquilado",
            )
        return self.get_roasted_coffee_by_id(roasted.id)

    def build_roasted_coffee_in_transaction(
        self,
        process_id: int,
        observations: Optional[str],
        details: List[DetailRoastedCoffeeCreate],
    ) -> "RoastedCoffee":
        """
        Construye el maquilado dentro de una transacción externa.
        NO hace commit ni rollback — el caller controla la transacción.
        """
        self._check_duplicate_process(process_id)
        return self._build_roasted_coffee(process_id, observations, details)

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def update_roasted_coffee(
        self, roasted_coffee_id: int, payload: RoastedCoffeeUpdate
    ) -> RoastedCoffeeInventoryResponse:
        roasted = (
            self.db.query(RoastedCoffee)
            .options(joinedload(RoastedCoffee.details))
            .filter(RoastedCoffee.id == roasted_coffee_id)
            .first()
        )
        if not roasted:
            raise HTTPException(status_code=404, detail="Maquilado no encontrado")

        try:
            roasted.observations = payload.observations

            details_map = {d.id: d for d in roasted.details}

            for item in payload.details:
                detail = details_map.get(item.id)
                if not detail:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Detalle {item.id} no encontrado",
                    )

                previous = detail.remaining_quantity
                new_qty = item.remaining_quantity

                if new_qty != previous:
                    delta = new_qty - previous
                    movement_type = (
                        MovementTypeEnum.processed_entrance
                        if delta > 0
                        else MovementTypeEnum.processed_exit
                    )
                    movement = InventoryMovement(
                        movement_date=datetime.now(),
                        movement_type=movement_type,
                        product_type=ProductMovementTypeEnum.processed,
                        process_id=roasted.process_id,
                        quantity=Decimal(abs(delta)),
                        reason="Ajuste manual de cantidad restante",
                        observations=(
                            f"Maquilado #{roasted_coffee_id} · "
                            f"detalle #{detail.id} · "
                            f"anterior={previous} -> nuevo={new_qty}"
                        ),
                    )
                    self.db.add(movement)

                detail.remaining_quantity = new_qty

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el maquilado",
            )

        return self.get_roasted_coffee_by_id(roasted_coffee_id)

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def delete_roasted_coffee(
        self, roasted_coffee_id: int
    ) -> RoastedCoffeeDeleteResponse:
        roasted = (
            self.db.query(RoastedCoffee)
            .filter(RoastedCoffee.id == roasted_coffee_id)
            .first()
        )
        if not roasted:
            raise HTTPException(status_code=404, detail="Maquilado no encontrado")

        try:
            self.db.delete(roasted)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el maquilado",
            )

        return RoastedCoffeeDeleteResponse(
            message=f"Maquilado {roasted_coffee_id} eliminado correctamente"
        )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _check_duplicate_process(self, process_id: int) -> None:
        existing = (
            self.db.query(RoastedCoffee)
            .filter(RoastedCoffee.process_id == process_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este proceso ya tiene un maquilado registrado",
            )

    def _build_roasted_coffee(
        self,
        process_id: int,
        observations: Optional[str],
        details: List[DetailRoastedCoffeeCreate],
    ) -> "RoastedCoffee":
        """
        Agrega RoastedCoffee, sus detalles y los movimientos de entrada
        a la sesión con flush. Sin commit — el caller controla la transacción.
        """
        roasted = RoastedCoffee(
            process_id=process_id,
            observations=observations,
        )
        self.db.add(roasted)
        self.db.flush()

        for item in details:
            detail = DetailRoastedCoffee(
                roasted_coffee_id=roasted.id,
                product_id=item.product_id,
                quantity=item.quantity,
                remaining_quantity=item.quantity,
            )
            self.db.add(detail)

            movement = InventoryMovement(
                movement_date=datetime.now(),
                movement_type=MovementTypeEnum.processed_entrance,
                product_type=ProductMovementTypeEnum.processed,
                process_id=process_id,
                quantity=Decimal(item.quantity),
                reason="Entrada de café maquilado generada desde proceso",
                observations=(
                    f"Proceso #{process_id} · "
                    f"producto_id={item.product_id} · "
                    f"cantidad={item.quantity}"
                ),
            )
            self.db.add(movement)

        self.db.flush()
        return roasted

    def _base_query(self):
        return (
            self.db.query(RoastedCoffee)
            .join(DetailRoastedCoffee, DetailRoastedCoffee.roasted_coffee_id == RoastedCoffee.id)
            .join(Product, Product.id == DetailRoastedCoffee.product_id)
            .join(Process, Process.id == RoastedCoffee.process_id)
            .join(Parchment, Parchment.id == Process.parchment_id)
            .options(
                joinedload(RoastedCoffee.details).joinedload(DetailRoastedCoffee.product),
                joinedload(RoastedCoffee.process).joinedload(Process.parchment),
            )
        )

    @staticmethod
    def _to_response(roasted: RoastedCoffee) -> RoastedCoffeeInventoryResponse:
        variety = None
        if roasted.process and roasted.process.parchment:
            variety = roasted.process.parchment.variety

        return RoastedCoffeeInventoryResponse(
            id=roasted.id,
            process_id=roasted.process_id,
            variety=variety,
            observations=roasted.observations,
            products=[
                RoastedCoffeeProductResponse(
                    detail_id=d.id,
                    product_id=d.product.id,
                    name=d.product.name,
                    quantity=d.quantity,
                    remaining_quantity=d.remaining_quantity,
                )
                for d in roasted.details
            ],
        )
