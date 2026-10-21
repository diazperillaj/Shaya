from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.roasted_coffee.schema import (
    InventoryEventResponse,
    InventoryLotProductResponse,
    InventoryLotResponse,
    RoastedInventoryDashboardResponse,
)
from app.models.customer import Customer
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.fair import Fair, FairStatusEnum
from app.models.fair_inventory import FairInventory
from app.models.farmer import Farmer
from app.models.parchment import Parchment
from app.models.process import Process
from app.models.roasted_coffe import RoastedCoffee
from app.models.roasted_movement import MovementDirectionEnum, RoastedMovement, RoastedMovementDetail
from app.models.sale import Sale

# Las fechas del tablero son las del calendario en Colombia (UTC−5 todo el
# año): una venta a las 8 p. m. no debe caer en el día siguiente.
BUSINESS_TZ = timezone(timedelta(hours=-5), "America/Bogota")

# Orden de los eventos de un mismo día: primero lo que entra
KIND_ORDER = {"process": 0, "adjustment": 1, "movement": 2, "sale": 3, "fair": 4}


class RoastedCoffeeDashboardService:
    """
    Tablero del inventario de café maquilado: los lotes con su origen y la
    línea de tiempo de entradas y salidas de cada producto.

    Las salidas salen de sus tablas de origen: ventas directas, ferias y
    movimientos (envíos, bajas, reempaques). La venta consolidada que se
    genera al cerrar una feria no se cuenta aparte: sus unidades ya salieron
    del inventario al asignarlas a la feria.

    La existencia inicial de cada producto se deduce de su cantidad restante
    menos todo lo registrado después (restante − entradas + salidas), así la
    línea de tiempo cuadra siempre con el inventario actual. En los lotes
    creados desde el sistema coincide con la cantidad del proceso; en los
    importados del Excel las entradas vienen como movimientos.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self) -> RoastedInventoryDashboardResponse:
        roasted_coffees = (
            self.db.query(RoastedCoffee)
            .options(
                joinedload(RoastedCoffee.details).joinedload(DetailRoastedCoffee.product),
                joinedload(RoastedCoffee.process)
                .joinedload(Process.parchment)
                .joinedload(Parchment.farmer)
                .joinedload(Farmer.person),
            )
            .order_by(RoastedCoffee.id.desc())
            .all()
        )

        details: Dict[int, DetailRoastedCoffee] = {
            d.id: d for rc in roasted_coffees for d in rc.details
        }
        recorded = self._recorded_events(details)

        events: List[InventoryEventResponse] = []
        lots: List[InventoryLotResponse] = []
        for rc in roasted_coffees:
            process = rc.process
            parchment = process.parchment
            farmer = parchment.farmer

            products: List[InventoryLotProductResponse] = []
            for d in sorted(rc.details, key=lambda d: d.id):
                own = recorded.get(d.id, [])
                opening = d.remaining_quantity - sum(e.quantity for e in own)
                if opening != 0:
                    # Negativa solo si los datos no cuadran (salidas sin entrada)
                    own = [
                        self._event(
                            d,
                            process.process_date,
                            "process" if opening > 0 else "adjustment",
                            opening,
                            f"Factura {process.invoice_number}",
                            None if opening > 0 else "Diferencia sin movimiento registrado",
                        )
                    ] + own
                events.extend(own)

                products.append(
                    InventoryLotProductResponse(
                        detail_id=d.id,
                        product_id=d.product_id,
                        name=d.product.name,
                        total_in=sum(e.quantity for e in own if e.quantity > 0),
                        total_out=-sum(e.quantity for e in own if e.quantity < 0),
                        remaining_quantity=d.remaining_quantity,
                        unit_cost=float(d.unit_cost) if d.unit_cost is not None else None,
                    )
                )

            lots.append(
                InventoryLotResponse(
                    id=rc.id,
                    process_id=rc.process_id,
                    invoice_number=process.invoice_number,
                    process_date=process.process_date,
                    variety=parchment.variety,
                    farmer_name=farmer.person.full_name if farmer.person else None,
                    farm_name=farmer.farm_name,
                    altitude=self._float(parchment.altitude),
                    yield_percentage=self._float(process.yield_percentage),
                    observations=rc.observations,
                    products=products,
                )
            )

        events.sort(key=lambda e: (e.event_date, KIND_ORDER[e.kind], e.lot_id, e.detail_id))
        return RoastedInventoryDashboardResponse(lots=lots, events=events)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _recorded_events(
        self, details: Dict[int, DetailRoastedCoffee]
    ) -> Dict[int, List[InventoryEventResponse]]:
        """Ventas, ferias y movimientos registrados, agrupados por producto de lote."""
        by_detail: Dict[int, List[InventoryEventResponse]] = defaultdict(list)

        def add(drc_id: int, *args) -> None:
            detail = details.get(drc_id)
            if detail is not None:
                by_detail[drc_id].append(self._event(detail, *args))

        consolidated_sales = select(Fair.sale_id).where(Fair.sale_id.isnot(None))
        sale_lines = (
            self.db.query(DetailSale)
            .join(Sale, Sale.id == DetailSale.sale_id)
            .filter(Sale.id.not_in(consolidated_sales))
            .options(joinedload(DetailSale.sale).joinedload(Sale.customer).joinedload(Customer.person))
            .all()
        )
        for line in sale_lines:
            sale = line.sale
            customer = sale.customer.person.full_name if sale.customer and sale.customer.person else None
            add(line.detail_roasted_coffee_id, sale.sale_date, "sale", -line.quantity, f"Venta #{sale.id}", customer)

        fair_lines = self.db.query(FairInventory).options(joinedload(FairInventory.fair)).all()
        for line in fair_lines:
            fair = line.fair
            is_open = fair.status == FairStatusEnum.open
            # Feria abierta: todo lo asignado está fuera de bodega; cerrada:
            # solo lo vendido, el sobrante ya volvió al cerrar.
            used = line.initial_quantity if is_open else line.initial_quantity - line.remaining_quantity
            if used:
                add(
                    line.detail_roasted_coffee_id,
                    self._local_date(fair.start_datetime),
                    "fair",
                    -used,
                    fair.name,
                    "En curso" if is_open else fair.location,
                )

        movement_lines = (
            self.db.query(RoastedMovementDetail)
            .options(joinedload(RoastedMovementDetail.movement))
            .all()
        )
        for line in movement_lines:
            movement: RoastedMovement = line.movement
            is_entry = line.direction == MovementDirectionEnum.entry
            add(
                line.detail_roasted_coffee_id,
                self._local_date(movement.movement_date),
                "movement",
                line.quantity if is_entry else -line.quantity,
                f"Movimiento #{movement.id}",
                movement.observations,
            )

        return by_detail

    @staticmethod
    def _event(
        detail: DetailRoastedCoffee,
        event_date: date,
        kind: str,
        quantity: int,
        reference: str,
        note: Optional[str],
    ) -> InventoryEventResponse:
        return InventoryEventResponse(
            event_date=event_date,
            lot_id=detail.roasted_coffee_id,
            detail_id=detail.id,
            product_id=detail.product_id,
            product_name=detail.product.name,
            kind=kind,
            quantity=quantity,
            reference=reference,
            note=note,
        )

    @staticmethod
    def _local_date(moment: datetime) -> date:
        return moment.astimezone(BUSINESS_TZ).date()

    @staticmethod
    def _float(value) -> Optional[float]:
        return float(value) if value is not None else None
