from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.detail_process import DetailProcess
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.process import Process
from app.models.process_expense import ProcessExpense
from app.models.product_expense import ProductExpense
from app.models.roasted_coffe import RoastedCoffee


class ProcessCostService:
    """
    Servicio de costos de producción.

    Única fuente de la fórmula del costo por bolsa (unit_cost):

        costo_pergamino  = (parchment_kg * purchase_price) / initial_quantity
                           (regla de 3: si initial_quantity kg costaron
                           purchase_price, cuánto valen los parchment_kg usados)
        costo_por_gramo  = (costo_pergamino + gastos_del_proceso) / gramos_embolsados
        unit_cost        = grams_per_bag * costo_por_gramo      <- café + gastos proceso
                         + total_linea_maquila / bag_quantity   <- maquila con IVA
                         + costos_del_producto                  <- empaque etc., por bolsa

    Los costos de producto se toman con su valor vigente al momento del
    cálculo; los lotes ya calculados conservan su costo histórico salvo
    que se recalculen explícitamente.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Cálculo y escritura de unit_cost
    # ------------------------------------------------------------------

    def recalculate_process_costs(self, process_id: int) -> int:
        """
        Recalcula el unit_cost de todos los lotes (DetailRoastedCoffee)
        del proceso. Hace flush, sin commit: el caller controla la
        transacción.

        Returns:
            int: cantidad de lotes actualizados.
        """
        process = self._get_process_with_relations(process_id)
        if not process or not process.details:
            return 0

        unit_costs = self._compute_unit_costs(process)
        if not unit_costs:
            return 0

        updated = 0
        for detail in self._get_roasted_details(process_id):
            unit_cost = unit_costs.get(detail.product_id)
            if unit_cost is not None:
                detail.unit_cost = unit_cost
                updated += 1

        self.db.flush()
        return updated

    # ------------------------------------------------------------------
    # Desglose de costos para GET /process/{id}/costs
    # ------------------------------------------------------------------

    def get_process_costs(self, process_id: int) -> dict:
        """
        Devuelve el desglose completo de costos de un proceso:
        pergamino, maquila, gastos del proceso, y por producto sus
        costos de producción y unit_cost.
        """
        process = self._get_process_with_relations(process_id)
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found",
            )

        parchment = process.parchment
        parchment_cost = self._parchment_cost(process)
        total_grams = self._total_grams(process)

        expenses = self._get_process_expenses(process_id)
        expenses_total = sum((e.amount for e in expenses), Decimal("0"))

        cost_per_gram = (
            (parchment_cost + expenses_total) / total_grams
            if total_grams > 0
            else Decimal("0")
        )

        product_expenses = self._get_product_expenses(
            [d.product_id for d in process.details]
        )
        roasted_by_product = {
            d.product_id: d for d in self._get_roasted_details(process_id)
        }

        products: List[dict] = []
        total_cost = parchment_cost + expenses_total
        for line in process.details:
            line_product_expenses = product_expenses.get(line.product_id, [])
            product_expenses_per_bag = sum(
                (e.amount for e in line_product_expenses), Decimal("0")
            )
            roasted = roasted_by_product.get(line.product_id)
            unit_cost = roasted.unit_cost if roasted else None

            line_total_cost = (
                unit_cost * line.bag_quantity if unit_cost is not None else None
            )
            total_cost += Decimal(line.total) + (
                product_expenses_per_bag * line.bag_quantity
            )

            products.append(
                {
                    "product_id": line.product_id,
                    "product_name": line.product.name if line.product else None,
                    "bag_quantity": line.bag_quantity,
                    "grams_per_bag": line.grams_per_bag,
                    "maquila_unit_value": line.unit_value,
                    "maquila_line_total": line.total,
                    "product_expenses": [
                        {
                            "id": e.id,
                            "category": e.category.value,
                            "amount": e.amount,
                            "observations": e.observations,
                        }
                        for e in line_product_expenses
                    ],
                    "product_expenses_per_bag": self._round_money(
                        product_expenses_per_bag
                    ),
                    "unit_cost": unit_cost,
                    "total_cost": (
                        self._round_money(line_total_cost)
                        if line_total_cost is not None
                        else None
                    ),
                }
            )

        return {
            "process_id": process.id,
            "invoice_number": process.invoice_number,
            "process_date": process.process_date,
            "parchment": {
                "parchment_id": process.parchment_id,
                "variety": parchment.variety if parchment else None,
                "parchment_kg": process.parchment_kg,
                "lot_initial_quantity": parchment.initial_quantity if parchment else None,
                "lot_purchase_price": parchment.purchase_price if parchment else None,
                "cost": self._round_money(parchment_cost),
            },
            "maquila": {
                "subtotal": process.subtotal,
                "iva": process.iva,
                "total": process.total,
            },
            "process_expenses": [
                {
                    "id": e.id,
                    "category": e.category.value,
                    "amount": e.amount,
                    "expense_date": e.expense_date,
                    "observations": e.observations,
                }
                for e in expenses
            ],
            "process_expenses_total": self._round_money(expenses_total),
            "total_grams": total_grams,
            "cost_per_gram": (
                cost_per_gram.quantize(Decimal("0.0001"))
                if total_grams > 0
                else None
            ),
            "total_cost": self._round_money(total_cost),
            "products": products,
        }

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _compute_unit_costs(self, process: Process) -> Dict[int, Decimal]:
        """
        Calcula el unit_cost por producto del proceso.
        Si un producto tiene varias líneas, se promedia ponderado por bolsas.
        """
        total_grams = self._total_grams(process)
        if total_grams <= 0:
            return {}

        parchment_cost = self._parchment_cost(process)
        expenses = self._get_process_expenses(process.id)
        expenses_total = sum((e.amount for e in expenses), Decimal("0"))

        cost_per_gram = (parchment_cost + expenses_total) / total_grams

        # Acumular por producto: café + gastos proceso + maquila (con IVA)
        totals: Dict[int, dict] = {}
        for line in process.details:
            bags = Decimal(line.bag_quantity)
            if bags <= 0:
                continue
            coffee_cost = Decimal(line.grams_per_bag) * cost_per_gram * bags
            maquila_cost = Decimal(line.total)
            acc = totals.setdefault(
                line.product_id, {"cost": Decimal("0"), "bags": Decimal("0")}
            )
            acc["cost"] += coffee_cost + maquila_cost
            acc["bags"] += bags

        product_expenses = self._get_product_expenses(list(totals.keys()))

        unit_costs: Dict[int, Decimal] = {}
        for product_id, acc in totals.items():
            if acc["bags"] <= 0:
                continue
            per_bag_expenses = sum(
                (e.amount for e in product_expenses.get(product_id, [])),
                Decimal("0"),
            )
            unit_cost = acc["cost"] / acc["bags"] + per_bag_expenses
            unit_costs[product_id] = self._round_money(unit_cost)

        return unit_costs

    def _get_process_with_relations(self, process_id: int) -> Optional[Process]:
        return (
            self.db.query(Process)
            .options(
                joinedload(Process.parchment),
                joinedload(Process.details).joinedload(DetailProcess.product),
            )
            .filter(Process.id == process_id)
            .first()
        )

    def _get_roasted_details(self, process_id: int) -> List[DetailRoastedCoffee]:
        return (
            self.db.query(DetailRoastedCoffee)
            .join(
                RoastedCoffee,
                DetailRoastedCoffee.roasted_coffee_id == RoastedCoffee.id,
            )
            .filter(RoastedCoffee.process_id == process_id)
            .all()
        )

    def _get_process_expenses(self, process_id: int) -> List[ProcessExpense]:
        return (
            self.db.query(ProcessExpense)
            .filter(ProcessExpense.process_id == process_id)
            .all()
        )

    def _get_product_expenses(
        self, product_ids: List[int]
    ) -> Dict[int, List[ProductExpense]]:
        if not product_ids:
            return {}
        expenses = (
            self.db.query(ProductExpense)
            .filter(ProductExpense.product_id.in_(product_ids))
            .all()
        )
        grouped: Dict[int, List[ProductExpense]] = {}
        for e in expenses:
            grouped.setdefault(e.product_id, []).append(e)
        return grouped

    @staticmethod
    def _total_grams(process: Process) -> Decimal:
        return sum(
            (
                Decimal(d.bag_quantity) * Decimal(d.grams_per_bag)
                for d in process.details
            ),
            Decimal("0"),
        )

    @staticmethod
    def _parchment_cost(process: Process) -> Decimal:
        """Regla de 3 sobre el lote de pergamino usado."""
        parchment = process.parchment
        if (
            not parchment
            or not parchment.initial_quantity
            or Decimal(parchment.initial_quantity) <= 0
        ):
            return Decimal("0")
        return (
            Decimal(process.parchment_kg) * Decimal(parchment.purchase_price)
        ) / Decimal(parchment.initial_quantity)

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))
