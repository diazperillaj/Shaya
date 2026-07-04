from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.fairs.schema import (
    FairCreate,
    FairExpenseCreate,
    FairExpenseUpdate,
    FairInventoryCreate,
    FairInventoryUpdate,
    FairSaleCreate,
    FairSaleUpdate,
    FairUpdate,
)
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.fair import Fair, FairStatusEnum
from app.models.fair_expense import ExpenseCategoryEnum, FairExpense
from app.models.fair_inventory import FairInventory
from app.models.fair_sale import FairSale
from app.models.inventory_movement import InventoryMovement, MovementTypeEnum, ProductMovementTypeEnum
from app.models.product import Product
from app.models.sale import Sale, SaleStatusEnum
from app.models.user import User


class FairService:
    def __init__(self, db: Session):
        self.db = db

    # ═══════════════════════════════════════════════════════════════════════════
    # FAIRS CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def get_fairs(self, search: Optional[str] = None) -> List[Fair]:
        query = (
            self.db.query(Fair)
            .options(
                joinedload(Fair.user).joinedload(User.person),
                joinedload(Fair.inventory)
                    .joinedload(FairInventory.detail_roasted_coffee)
                    .joinedload(DetailRoastedCoffee.product),
                joinedload(Fair.fair_sales)
                    .joinedload(FairSale.fair_inventory)
                    .joinedload(FairInventory.detail_roasted_coffee)
                    .joinedload(DetailRoastedCoffee.product),
                joinedload(Fair.expenses).joinedload(FairExpense.user).joinedload(User.person),
            )
        )
        if search:
            query = query.filter(
                Fair.name.ilike(f"%{search}%") |
                Fair.location.ilike(f"%{search}%")
            )
        return query.order_by(desc(Fair.id)).all()

    def get_fair_by_id(self, fair_id: int) -> Fair:
        fair = (
            self.db.query(Fair)
            .options(
                joinedload(Fair.user).joinedload(User.person),
                joinedload(Fair.inventory)
                    .joinedload(FairInventory.detail_roasted_coffee)
                    .joinedload(DetailRoastedCoffee.product),
                joinedload(Fair.fair_sales)
                    .joinedload(FairSale.fair_inventory)
                    .joinedload(FairInventory.detail_roasted_coffee)
                    .joinedload(DetailRoastedCoffee.product),
                joinedload(Fair.expenses).joinedload(FairExpense.user).joinedload(User.person),
            )
            .filter(Fair.id == fair_id)
            .first()
        )
        if not fair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feria no encontrada")
        return fair

    def create_fair(self, payload: FairCreate, current_user: User) -> Fair:
        try:
            fair = Fair(
                name=payload.name,
                location=payload.location,
                start_datetime=payload.start_datetime,
                status=FairStatusEnum.open,
                user_id=current_user.id,
                observations=payload.observations,
            )
            self.db.add(fair)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al crear la feria",
            )
        return self.get_fair_by_id(fair.id)

    def update_fair(self, fair_id: int, payload: FairUpdate, current_user: User) -> Fair:
        fair = self._get_fair_or_404(fair_id)
        self._require_open(fair)

        try:
            fair.name = payload.name
            fair.location = payload.location
            fair.start_datetime = payload.start_datetime
            fair.observations = payload.observations
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar la feria",
            )
        return self.get_fair_by_id(fair_id)

    def delete_fair(self, fair_id: int) -> bool:
        """
        Elimina una feria (abierta o cerrada) deshaciendo todo su efecto,
        como si nunca hubiera existido:

        - Devuelve al stock general lo que aún falte por devolver:
          · feria abierta: todo lo asignado (sobrante + vendido), porque
            nada ha vuelto al stock todavía.
          · feria cerrada: solo lo vendido (initial - remaining), porque
            el sobrante ya se devolvió al cerrar.
        - Elimina la venta consolidada generada al cierre (si existe).
        - El cascade elimina inventario, ventas, gastos y movimientos
          de la feria.
        """
        fair = self._get_fair_or_404(fair_id)

        try:
            is_closed = fair.status == FairStatusEnum.closed
            for inv in fair.inventory:
                restore = (
                    inv.initial_quantity - inv.remaining_quantity
                    if is_closed
                    else inv.initial_quantity
                )
                if restore > 0:
                    drc = self._get_drc_or_404(inv.detail_roasted_coffee_id)
                    drc.remaining_quantity += restore

            consolidated_sale_id = fair.sale_id

            self.db.delete(fair)
            self.db.flush()

            if consolidated_sale_id:
                sale = (
                    self.db.query(Sale)
                    .filter(Sale.id == consolidated_sale_id)
                    .first()
                )
                if sale:
                    self.db.delete(sale)

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la feria",
            )
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # FAIR INVENTORY CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def create_fair_inventory(self, fair_id: int, payload: FairInventoryCreate, current_user: User) -> Fair:
        fair = self._get_fair_or_404(fair_id)
        self._require_open(fair)

        drc = self._get_drc_or_404(payload.detail_roasted_coffee_id)

        if payload.initial_quantity > drc.remaining_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock insuficiente. Disponible: {drc.remaining_quantity}, "
                    f"solicitado: {payload.initial_quantity}"
                ),
            )

        try:
            inv = FairInventory(
                fair_id=fair_id,
                detail_roasted_coffee_id=payload.detail_roasted_coffee_id,
                initial_quantity=payload.initial_quantity,
                remaining_quantity=payload.initial_quantity,
                unit_value=payload.unit_value,
            )
            self.db.add(inv)
            drc.remaining_quantity -= payload.initial_quantity
            self.db.flush()

            self.db.add(InventoryMovement(
                movement_type=MovementTypeEnum.fair_entrance,
                product_type=ProductMovementTypeEnum.processed,
                fair_id=fair_id,
                quantity=payload.initial_quantity,
                reason="Asignación de inventario a feria",
                responsible=f"user_id={current_user.id}",
                observations=f"Feria #{fair_id} — drc_id={drc.id}",
            ))
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al asignar inventario a la feria",
            )
        return self.get_fair_by_id(fair_id)

    def update_fair_inventory(
        self, fair_id: int, inv_id: int, payload: FairInventoryUpdate, current_user: User
    ) -> Fair:
        fair = self._get_fair_or_404(fair_id)
        self._require_open(fair)
        inv = self._get_fair_inventory_or_404(inv_id, fair_id)

        already_sold = inv.initial_quantity - inv.remaining_quantity
        if payload.initial_quantity < already_sold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No se puede reducir por debajo de las unidades ya vendidas ({already_sold})."
                ),
            )

        delta = payload.initial_quantity - inv.initial_quantity
        drc = self._get_drc_or_404(inv.detail_roasted_coffee_id)

        if delta > 0 and delta > drc.remaining_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock insuficiente para aumentar inventario. "
                    f"Disponible en general: {drc.remaining_quantity}, delta requerido: {delta}"
                ),
            )

        try:
            drc.remaining_quantity -= delta
            inv.initial_quantity = payload.initial_quantity
            inv.remaining_quantity = payload.initial_quantity - already_sold
            inv.unit_value = payload.unit_value

            movement_type = MovementTypeEnum.fair_entrance if delta > 0 else MovementTypeEnum.fair_return
            if delta != 0:
                self.db.add(InventoryMovement(
                    movement_type=movement_type,
                    product_type=ProductMovementTypeEnum.processed,
                    fair_id=fair_id,
                    quantity=abs(delta),
                    reason="Ajuste de inventario de feria",
                    responsible=f"user_id={current_user.id}",
                    observations=f"Feria #{fair_id} — drc_id={drc.id} — delta={delta}",
                ))
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el inventario de la feria",
            )
        return self.get_fair_by_id(fair_id)

    def delete_fair_inventory(self, fair_id: int, inv_id: int, current_user: User) -> Fair:
        self._get_fair_or_404(fair_id)
        inv = self._get_fair_inventory_or_404(inv_id, fair_id)

        has_sales = self.db.query(FairSale).filter(FairSale.fair_inventory_id == inv_id).first()
        if has_sales:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un ítem de inventario que ya tiene ventas registradas.",
            )

        drc = self._get_drc_or_404(inv.detail_roasted_coffee_id)

        try:
            drc.remaining_quantity += inv.initial_quantity
            self.db.add(InventoryMovement(
                movement_type=MovementTypeEnum.fair_return,
                product_type=ProductMovementTypeEnum.processed,
                fair_id=fair_id,
                quantity=inv.initial_quantity,
                reason="Eliminación de inventario de feria",
                responsible=f"user_id={current_user.id}",
                observations=f"Feria #{fair_id} — drc_id={drc.id}",
            ))
            self.db.delete(inv)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el inventario de la feria",
            )
        return self.get_fair_by_id(fair_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # FAIR SALES CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def create_fair_sale(self, fair_id: int, payload: FairSaleCreate, current_user: User) -> Fair:
        fair = self._get_fair_or_404(fair_id)
        self._require_open(fair)
        inv = self._get_fair_inventory_or_404(payload.fair_inventory_id, fair_id)

        if payload.quantity > inv.remaining_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock insuficiente en feria. Disponible: {inv.remaining_quantity}, "
                    f"solicitado: {payload.quantity}"
                ),
            )

        total = self._round(Decimal(payload.quantity) * payload.unit_value)
        sale_dt = payload.sale_datetime or datetime.now(timezone.utc)

        try:
            sale = FairSale(
                fair_id=fair_id,
                fair_inventory_id=payload.fair_inventory_id,
                sale_datetime=sale_dt,
                quantity=payload.quantity,
                unit_value=payload.unit_value,
                total=total,
                observations=payload.observations,
            )
            self.db.add(sale)
            inv.remaining_quantity -= payload.quantity
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al registrar la venta en feria",
            )
        return self.get_fair_by_id(fair_id)

    def update_fair_sale(
        self, fair_id: int, sale_id: int, payload: FairSaleUpdate, current_user: User
    ) -> Fair:
        self._get_fair_or_404(fair_id)
        sale = self._get_fair_sale_or_404(sale_id, fair_id)
        inv = self._get_fair_inventory_or_404(sale.fair_inventory_id, fair_id)

        # Restore old quantity then validate new
        available_after_restore = inv.remaining_quantity + sale.quantity
        if payload.quantity > available_after_restore:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Stock insuficiente. Disponible tras revertir: {available_after_restore}, "
                    f"solicitado: {payload.quantity}"
                ),
            )

        total = self._round(Decimal(payload.quantity) * payload.unit_value)
        sale_dt = payload.sale_datetime or sale.sale_datetime

        try:
            inv.remaining_quantity = available_after_restore - payload.quantity
            sale.fair_inventory_id = payload.fair_inventory_id
            sale.sale_datetime = sale_dt
            sale.quantity = payload.quantity
            sale.unit_value = payload.unit_value
            sale.total = total
            sale.observations = payload.observations
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar la venta en feria",
            )
        return self.get_fair_by_id(fair_id)

    def delete_fair_sale(self, fair_id: int, sale_id: int, current_user: User) -> Fair:
        self._get_fair_or_404(fair_id)
        sale = self._get_fair_sale_or_404(sale_id, fair_id)
        inv = self._get_fair_inventory_or_404(sale.fair_inventory_id, fair_id)

        try:
            inv.remaining_quantity += sale.quantity
            self.db.delete(sale)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la venta en feria",
            )
        return self.get_fair_by_id(fair_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # FAIR EXPENSES CRUD
    # ═══════════════════════════════════════════════════════════════════════════

    def create_fair_expense(self, fair_id: int, payload: FairExpenseCreate, current_user: User) -> Fair:
        fair = self._get_fair_or_404(fair_id)
        self._require_open(fair)

        expense_dt = payload.expense_datetime or datetime.now(timezone.utc)

        try:
            expense = FairExpense(
                fair_id=fair_id,
                user_id=current_user.id,
                category=ExpenseCategoryEnum(payload.category),
                description=payload.description,
                amount=payload.amount,
                expense_datetime=expense_dt,
            )
            self.db.add(expense)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al registrar el gasto",
            )
        return self.get_fair_by_id(fair_id)

    def update_fair_expense(
        self, fair_id: int, expense_id: int, payload: FairExpenseUpdate, current_user: User
    ) -> Fair:
        self._get_fair_or_404(fair_id)
        expense = self._get_fair_expense_or_404(expense_id, fair_id)

        expense_dt = payload.expense_datetime or expense.expense_datetime

        try:
            expense.category = ExpenseCategoryEnum(payload.category)
            expense.description = payload.description
            expense.amount = payload.amount
            expense.expense_datetime = expense_dt
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el gasto",
            )
        return self.get_fair_by_id(fair_id)

    def delete_fair_expense(self, fair_id: int, expense_id: int, current_user: User) -> Fair:
        self._get_fair_or_404(fair_id)
        expense = self._get_fair_expense_or_404(expense_id, fair_id)

        try:
            self.db.delete(expense)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el gasto",
            )
        return self.get_fair_by_id(fair_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # CLOSE FAIR
    # ═══════════════════════════════════════════════════════════════════════════

    def close_fair(self, fair_id: int, current_user: User) -> Fair:
        fair = self._get_fair_or_404(fair_id)
        self._require_open(fair)

        now = datetime.now(timezone.utc)

        try:
            # 1. Return remaining inventory to general stock
            for inv in fair.inventory:
                if inv.remaining_quantity > 0:
                    drc = self._get_drc_or_404(inv.detail_roasted_coffee_id)
                    drc.remaining_quantity += inv.remaining_quantity
                    self.db.add(InventoryMovement(
                        movement_type=MovementTypeEnum.fair_return,
                        product_type=ProductMovementTypeEnum.processed,
                        fair_id=fair_id,
                        quantity=inv.remaining_quantity,
                        reason="Devolución de inventario al cerrar feria",
                        responsible=f"user_id={current_user.id}",
                        observations=f"Cierre feria #{fair_id} — drc_id={drc.id}",
                    ))

            self.db.flush()

            # 2. Build consolidated Sale (customer_id=None, linked via Fair.sale_id)
            consolidated = self._build_consolidated_sale(fair, current_user.id, now)
            if consolidated:
                self.db.add(consolidated)
                self.db.flush()

            # 3. Seal the fair
            fair.status = FairStatusEnum.closed
            fair.end_datetime = now
            if consolidated:
                fair.sale_id = consolidated.id

            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al cerrar la feria",
            )
        return self.get_fair_by_id(fair_id)

    def _build_consolidated_sale(self, fair: Fair, user_id: int, close_dt: datetime) -> Optional[Sale]:
        if not fair.fair_sales:
            return None

        # Group FairSales by detail_roasted_coffee_id
        aggregated: dict[int, dict] = {}
        for fs in fair.fair_sales:
            drc_id = fs.fair_inventory.detail_roasted_coffee_id
            if drc_id not in aggregated:
                aggregated[drc_id] = {
                    "quantity": 0,
                    "total": Decimal("0"),
                    "unit_value": fs.unit_value,
                }
            aggregated[drc_id]["quantity"] += fs.quantity
            aggregated[drc_id]["total"] += fs.total

        total_sale = sum(v["total"] for v in aggregated.values())

        sale = Sale(
            customer_id=None,
            user_id=user_id,
            sale_date=close_dt.date(),
            status=SaleStatusEnum.completed,
            observations=f"Venta consolidada — Feria: {fair.name}",
            subtotal=self._round(total_sale),
            iva=Decimal("0.00"),
            total=self._round(total_sale),
        )
        self.db.add(sale)
        self.db.flush()

        for drc_id, data in aggregated.items():
            detail = DetailSale(
                sale_id=sale.id,
                detail_roasted_coffee_id=drc_id,
                quantity=data["quantity"],
                unit_value=data["unit_value"],
                iva_percentage=Decimal("0.00"),
                subtotal=self._round(data["total"]),
                iva=Decimal("0.00"),
                total=self._round(data["total"]),
            )
            self.db.add(detail)

        return sale

    # ═══════════════════════════════════════════════════════════════════════════
    # REPORT
    # ═══════════════════════════════════════════════════════════════════════════

    def get_fair_report(self, fair_id: int):
        from app.api.api_v1.fairs.schema import (
            BarChartData,
            ChartSeries,
            FairInventoryStatusItem,
            FairKPIs,
            FairReportResponse,
            FairResponse,
            PieChartData,
        )

        fair = self.get_fair_by_id(fair_id)

        # ── KPIs ──────────────────────────────────────────────────────────────
        total_sales = sum(fs.total for fs in fair.fair_sales) or Decimal("0")
        total_transactions = len(fair.fair_sales)
        avg_sale_value = (
            self._round(total_sales / total_transactions) if total_transactions else Decimal("0")
        )
        total_expenses = sum(e.amount for e in fair.expenses) or Decimal("0")
        net_profit = total_sales - total_expenses
        margin_pct = (
            self._round((net_profit / total_sales) * 100) if total_sales > 0 else Decimal("0")
        )

        total_bags_assigned = sum(i.initial_quantity for i in fair.inventory)
        total_bags_sold = sum(
            i.initial_quantity - i.remaining_quantity for i in fair.inventory
        )
        total_bags_remaining = sum(i.remaining_quantity for i in fair.inventory)
        inv_utilization = (
            self._round(Decimal(total_bags_sold) / Decimal(total_bags_assigned) * 100)
            if total_bags_assigned > 0
            else Decimal("0")
        )

        duration_hours: Optional[float] = None
        if fair.end_datetime:
            diff = fair.end_datetime - fair.start_datetime
            duration_hours = round(diff.total_seconds() / 3600, 2)

        kpis = FairKPIs(
            total_sales=self._round(total_sales),
            total_transactions=total_transactions,
            avg_sale_value=avg_sale_value,
            total_expenses=self._round(total_expenses),
            net_profit=self._round(net_profit),
            margin_percentage=margin_pct,
            total_bags_assigned=total_bags_assigned,
            total_bags_sold=total_bags_sold,
            total_bags_remaining=total_bags_remaining,
            inventory_utilization_percentage=inv_utilization,
            duration_hours=duration_hours,
        )

        # ── Sales by product ──────────────────────────────────────────────────
        product_sales: dict[str, dict] = {}
        for fs in fair.fair_sales:
            inv = fs.fair_inventory
            if inv and inv.detail_roasted_coffee and inv.detail_roasted_coffee.product:
                name = inv.detail_roasted_coffee.product.name
            else:
                name = f"Producto #{fs.fair_inventory_id}"
            if name not in product_sales:
                product_sales[name] = {"qty": 0, "revenue": Decimal("0")}
            product_sales[name]["qty"] += fs.quantity
            product_sales[name]["revenue"] += fs.total

        sales_by_product = BarChartData(
            labels=list(product_sales.keys()) or ["Sin ventas"],
            series=[
                ChartSeries(
                    name="Unidades vendidas",
                    data=[float(v["qty"]) for v in product_sales.values()] or [0.0],
                ),
                ChartSeries(
                    name="Ingresos ($)",
                    data=[float(v["revenue"]) for v in product_sales.values()] or [0.0],
                ),
            ],
        )

        # ── Sales timeline (by hour if ≤1 day, by date if multi-day) ─────────
        sales_timeline = self._build_sales_timeline(fair)

        # ── Expenses by category ──────────────────────────────────────────────
        CATEGORY_LABELS = {
            "food": "Alimentación",
            "supplies": "Insumos",
            "transport": "Transporte",
            "other": "Otros",
        }
        category_totals: dict[str, Decimal] = {k: Decimal("0") for k in CATEGORY_LABELS}
        for e in fair.expenses:
            cat = e.category.value if hasattr(e.category, "value") else str(e.category)
            if cat in category_totals:
                category_totals[cat] += e.amount

        expenses_by_category = PieChartData(
            labels=[CATEGORY_LABELS[k] for k in category_totals],
            data=[float(v) for v in category_totals.values()],
        )

        # ── Inventory status per product ──────────────────────────────────────
        inventory_status = []
        for inv in fair.inventory:
            sold = inv.initial_quantity - inv.remaining_quantity
            inv_revenue = sum(
                fs.total for fs in fair.fair_sales if fs.fair_inventory_id == inv.id
            )
            utilization = (
                self._round(Decimal(sold) / Decimal(inv.initial_quantity) * 100)
                if inv.initial_quantity > 0
                else Decimal("0")
            )
            product_name = (
                inv.detail_roasted_coffee.product.name
                if inv.detail_roasted_coffee and inv.detail_roasted_coffee.product
                else f"DRC #{inv.detail_roasted_coffee_id}"
            )
            inventory_status.append(
                FairInventoryStatusItem(
                    product_name=product_name,
                    detail_roasted_coffee_id=inv.detail_roasted_coffee_id,
                    initial_quantity=inv.initial_quantity,
                    sold_quantity=sold,
                    remaining_quantity=inv.remaining_quantity,
                    utilization_percentage=utilization,
                    revenue=self._round(inv_revenue),
                )
            )

        return FairReportResponse(
            fair=FairResponse.model_validate(fair),
            kpis=kpis,
            sales_by_product=sales_by_product,
            sales_timeline=sales_timeline,
            expenses_by_category=expenses_by_category,
            inventory_status=inventory_status,
        )

    def _build_sales_timeline(self, fair: Fair):
        from app.api.api_v1.fairs.schema import BarChartData, ChartSeries

        if not fair.fair_sales:
            return BarChartData(
                labels=["Sin ventas"],
                series=[
                    ChartSeries(name="Ingresos ($)", data=[0.0]),
                    ChartSeries(name="N° ventas", data=[0.0]),
                ],
            )

        # Determine grouping: by hour if span ≤ 24h, otherwise by date
        dates = [fs.sale_datetime for fs in fair.fair_sales]
        span_hours = (max(dates) - min(dates)).total_seconds() / 3600

        if span_hours <= 24:
            # Group by hour (0-23)
            buckets: dict[str, dict] = {}
            for fs in sorted(fair.fair_sales, key=lambda x: x.sale_datetime):
                label = fs.sale_datetime.strftime("%H:00")
                if label not in buckets:
                    buckets[label] = {"revenue": Decimal("0"), "count": 0}
                buckets[label]["revenue"] += fs.total
                buckets[label]["count"] += 1
        else:
            # Group by date
            buckets = {}
            for fs in sorted(fair.fair_sales, key=lambda x: x.sale_datetime):
                label = fs.sale_datetime.strftime("%d/%m")
                if label not in buckets:
                    buckets[label] = {"revenue": Decimal("0"), "count": 0}
                buckets[label]["revenue"] += fs.total
                buckets[label]["count"] += 1

        return BarChartData(
            labels=list(buckets.keys()),
            series=[
                ChartSeries(
                    name="Ingresos ($)",
                    data=[float(v["revenue"]) for v in buckets.values()],
                ),
                ChartSeries(
                    name="N° ventas",
                    data=[float(v["count"]) for v in buckets.values()],
                ),
            ],
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_fair_or_404(self, fair_id: int) -> Fair:
        fair = (
            self.db.query(Fair)
            .options(
                joinedload(Fair.inventory).joinedload(FairInventory.detail_roasted_coffee),
                joinedload(Fair.fair_sales).joinedload(FairSale.fair_inventory),
                joinedload(Fair.expenses),
            )
            .filter(Fair.id == fair_id)
            .first()
        )
        if not fair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feria no encontrada")
        return fair

    def _get_fair_inventory_or_404(self, inv_id: int, fair_id: int) -> FairInventory:
        inv = (
            self.db.query(FairInventory)
            .filter(FairInventory.id == inv_id, FairInventory.fair_id == fair_id)
            .first()
        )
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ítem de inventario {inv_id} no encontrado en esta feria",
            )
        return inv

    def _get_fair_sale_or_404(self, sale_id: int, fair_id: int) -> FairSale:
        sale = (
            self.db.query(FairSale)
            .filter(FairSale.id == sale_id, FairSale.fair_id == fair_id)
            .first()
        )
        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venta {sale_id} no encontrada en esta feria",
            )
        return sale

    def _get_fair_expense_or_404(self, expense_id: int, fair_id: int) -> FairExpense:
        expense = (
            self.db.query(FairExpense)
            .filter(FairExpense.id == expense_id, FairExpense.fair_id == fair_id)
            .first()
        )
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gasto {expense_id} no encontrado en esta feria",
            )
        return expense

    def _get_drc_or_404(self, drc_id: int) -> DetailRoastedCoffee:
        drc = self.db.query(DetailRoastedCoffee).filter(DetailRoastedCoffee.id == drc_id).first()
        if not drc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lote de café tostado id={drc_id} no encontrado",
            )
        return drc

    def _require_open(self, fair: Fair) -> None:
        if fair.status != FairStatusEnum.open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta feria ya está cerrada. No se pueden realizar modificaciones.",
            )

    @staticmethod
    def _round(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))
