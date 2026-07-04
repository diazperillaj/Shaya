from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.sales.schema import SaleCreate, SaleUpdate
from app.models.customer import Customer
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.inventory_movement import InventoryMovement, MovementTypeEnum, ProductMovementTypeEnum
from app.models.sale import Sale, SaleStatusEnum
from app.models.user import User


class SaleService:
    def __init__(self, db: Session):
        self.db = db

    # ─── Queries ──────────────────────────────────────────────────────────────

    def get_sales(self, search: Optional[str] = None) -> List[Sale]:
        query = (
            self.db.query(Sale)
            .options(
                joinedload(Sale.customer).joinedload(Customer.person),
                joinedload(Sale.user).joinedload(User.person),
            )
        )
        if search:
            query = query.join(Sale.customer).join(Customer.person).filter(
                or_(
                    Sale.status.ilike(f"%{search}%"),
                )
            )
        return query.order_by(desc(Sale.id)).all()

    def get_sale_by_id(self, sale_id: int) -> Sale:
        sale = (
            self.db.query(Sale)
            .options(
                joinedload(Sale.customer).joinedload(Customer.person),
                joinedload(Sale.user).joinedload(User.person),
                joinedload(Sale.details)
                    .joinedload(DetailSale.detail_roasted_coffee)
                    .joinedload(DetailRoastedCoffee.product),
            )
            .filter(Sale.id == sale_id)
            .first()
        )
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        return sale

    # ─── Create ───────────────────────────────────────────────────────────────

    def create_sale(self, payload: SaleCreate, current_user: User) -> Sale:
        user_id = self._resolve_user_id(payload, current_user)
        self._get_customer_or_404(payload.customer_id)
        sale_date = self._parse_date(payload.sale_date)
        sale_status = SaleStatusEnum(payload.status)

        detail_rows, sale_subtotal, sale_iva = self._build_details(payload.details)

        sale_total = self._round(sale_subtotal + sale_iva)

        try:
            sale = Sale(
                customer_id=payload.customer_id,
                user_id=user_id,
                sale_date=sale_date,
                status=sale_status,
                observations=payload.observations,
                subtotal=self._round(sale_subtotal),
                iva=self._round(sale_iva),
                total=sale_total,
            )
            self.db.add(sale)
            self.db.flush()

            for drc, qty, detail in detail_rows:
                detail.sale_id = sale.id
                drc.remaining_quantity -= qty
                self.db.add(detail)
                self.db.add(InventoryMovement(
                    movement_type=MovementTypeEnum.processed_exit,
                    product_type=ProductMovementTypeEnum.processed,
                    sale_id=sale.id,
                    quantity=qty,
                    reason="Venta de café tostado",
                    responsible=f"user_id={user_id}",
                    observations=(
                        f"Venta #{sale.id} — producto detail_roasted_coffee_id={drc.id}"
                    ),
                ))

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear la venta",
            )

        return self.get_sale_by_id(sale.id)

    # ─── Update ───────────────────────────────────────────────────────────────

    def update_sale(self, sale_id: int, payload: SaleUpdate, current_user: User) -> Sale:
        sale = self.db.query(Sale).options(joinedload(Sale.details)).filter(Sale.id == sale_id).first()
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        user_id = self._resolve_user_id(payload, current_user)
        self._get_customer_or_404(payload.customer_id)
        sale_date = self._parse_date(payload.sale_date)
        sale_status = SaleStatusEnum(payload.status)

        detail_rows, sale_subtotal, sale_iva = self._build_details(payload.details)
        sale_total = self._round(sale_subtotal + sale_iva)

        try:
            # Restore inventory from old details and delete old movements
            for old_detail in sale.details:
                drc = self.db.query(DetailRoastedCoffee).get(old_detail.detail_roasted_coffee_id)
                if drc:
                    drc.remaining_quantity += old_detail.quantity

            # Cascade deletes DetailSale rows and their linked movements
            sale.details.clear()
            sale.movements.clear()
            self.db.flush()

            # Apply new details, deductions and movements
            for drc, qty, detail in detail_rows:
                detail.sale_id = sale.id
                drc.remaining_quantity -= qty
                self.db.add(detail)
                self.db.add(InventoryMovement(
                    movement_type=MovementTypeEnum.processed_exit,
                    product_type=ProductMovementTypeEnum.processed,
                    sale_id=sale.id,
                    quantity=qty,
                    reason="Actualización de venta — salida de café tostado",
                    responsible=f"user_id={user_id}",
                    observations=(
                        f"Venta #{sale.id} actualizada — detail_roasted_coffee_id={drc.id}"
                    ),
                ))

            sale.customer_id = payload.customer_id
            sale.user_id = user_id
            sale.sale_date = sale_date
            sale.status = sale_status
            sale.observations = payload.observations
            sale.subtotal = self._round(sale_subtotal)
            sale.iva = self._round(sale_iva)
            sale.total = sale_total

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar la venta",
            )

        return self.get_sale_by_id(sale.id)

    # ─── Delete ───────────────────────────────────────────────────────────────

    def delete_sale(self, sale_id: int) -> bool:
        sale = self.db.query(Sale).options(joinedload(Sale.details)).filter(Sale.id == sale_id).first()
        if not sale:
            return False

        try:
            for detail in sale.details:
                drc = self.db.query(DetailRoastedCoffee).get(detail.detail_roasted_coffee_id)
                if drc:
                    drc.remaining_quantity += detail.quantity

            self.db.delete(sale)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la venta",
            )

        return True

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _resolve_user_id(self, payload: SaleCreate, current_user: User) -> int:
        if current_user.role == "admin" and payload.user_id is not None:
            self._get_user_or_404(payload.user_id)
            return payload.user_id
        return current_user.id

    def _build_details(self, items):
        """
        Validates stock, computes line financials, and returns:
        (list of (drc_instance, qty, DetailSale), total_subtotal, total_iva)
        """
        detail_rows = []
        total_subtotal = Decimal("0")
        total_iva = Decimal("0")

        for item in items:
            
            drc = self._get_drc_or_404(item.detail_roasted_coffee_id)
            
            if item.quantity > drc.remaining_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Stock insuficiente para el ítem {drc.product_id}. "
                        f"Disponible: {drc.remaining_quantity}, solicitado: {item.quantity}"
                    ),
                )

            line_subtotal = self._round(Decimal(item.quantity) * item.unit_value)
            line_iva = self._round(line_subtotal * (item.iva_percentage / Decimal("100")))
            line_total = self._round(line_subtotal + line_iva)

            total_subtotal += line_subtotal
            total_iva += line_iva

            detail_rows.append((
                drc,
                item.quantity,
                DetailSale(
                    detail_roasted_coffee_id=item.detail_roasted_coffee_id,
                    quantity=item.quantity,
                    unit_value=item.unit_value,
                    iva_percentage=item.iva_percentage,
                    subtotal=line_subtotal,
                    iva=line_iva,
                    total=line_total,
                ),
            ))

        return detail_rows, total_subtotal, total_iva

    def _get_customer_or_404(self, customer_id: int) -> Customer:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
        return customer

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

    def _get_drc_or_404(self, drc_id: int) -> DetailRoastedCoffee:
        drc = self.db.query(DetailRoastedCoffee).filter(DetailRoastedCoffee.id == drc_id).first()
        if not drc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote de café tostado con id={drc_id} no encontrado",
            )
        return drc

    @staticmethod
    def _parse_date(raw: str):
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha debe estar en formato YYYY-MM-DD",
            )

    @staticmethod
    def _round(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))
