from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.api.api_v1.processes.cost_service import ProcessCostService
from app.api.api_v1.processes.schema import ProcessCreate, ProcessUpdate
from app.models.detail_process import DetailProcess
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.fair import Fair
from app.models.fair_inventory import FairInventory
from app.models.parchment import Parchment
from app.models.process import Process
from app.models.process_expense import ProcessExpense
from app.models.product import Product
from app.models.roasted_coffe import RoastedCoffee
from app.models.roasted_movement import RoastedMovementDetail

from app.api.api_v1.roasted_coffee.schema import DetailRoastedCoffeeCreate
from app.api.api_v1.roasted_coffee.service import RoastedCoffeeService
from app.api.api_v1.inventory.schema import ParchmentInventoryAdjustment
from app.api.api_v1.inventory.service import ParchmentService

IVA_RATE = Decimal("0.052")


class ProcessService:
    """Servicio de negocio para procesos (encabezado y detalles)."""

    def __init__(self, db: Session):
        self.db = db


    def test(self):
        prueba = self.db.query(Process).options(
            joinedload(Process.parchment),
            joinedload(Process.details).joinedload(DetailProcess.product),
        ).all()
        return prueba


    def get_processes(self, search: Optional[str] = None) -> List[Process]:
        """
        Lista procesos ordenados por ID descendente.
        Permite filtrar por numero de factura.
        """
        query = self.db.query(Process).options(
            joinedload(Process.parchment).joinedload(Parchment.farmer)
        )

        if search:
            query = query.filter(or_(Process.invoice_number.ilike(f"%{search}%")))

        return query.order_by(desc(Process.id)).all()


    def get_process_by_id(self, process_id: int) -> Process:
        """Obtiene un proceso por ID con pergamino y detalles."""
        process = (
            self.db.query(Process)
            .options(
                joinedload(Process.parchment),
                joinedload(Process.details).joinedload(DetailProcess.product),
            )
            .filter(Process.id == process_id)
            .first()
        )
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found",
            )
        return process


    def create_process(self, payload: ProcessCreate) -> Process:
        """
        Crea un proceso con sus detalles en una sola transacción atómica.
        Si algún producto genera inventario, también crea el RoastedCoffee
        asociado dentro del mismo commit.
        """
        
        
        
        # ── Bloque 1: proceso + detalles + roasted coffee (una sola transacción) ──
        try:
            process_date = self._parse_process_date(payload.process_date)
            parchment = self._get_parchment_or_404(payload.parchment_id)
            self._validate_parchment_quantity(parchment, payload.parchment_kg)

            resultant_kg, subtotal = self._calculate_totals(payload)
            process_iva = self._round_money(subtotal * IVA_RATE)
            process_total = self._round_money(subtotal + process_iva)
            yield_percentage = self._calculate_yield(resultant_kg, payload.parchment_kg)

            # 1. Flush del proceso para obtener process.id
            process = Process(
                invoice_number=payload.invoice_number.strip(),
                process_date=process_date,
                parchment_id=payload.parchment_id,
                parchment_kg=payload.parchment_kg,
                resultant_kg=resultant_kg,
                yield_percentage=yield_percentage,
                subtotal=subtotal,
                iva=process_iva,
                total=process_total,
                observations=payload.observations,
            )
            
            
            
            self.db.add(process)
            self.db.flush()  # process.id disponible desde aquí

            # 2. Detalles del proceso + acumular los que generan inventario
            details: List[DetailProcess] = []
            roasted_details: List[DetailRoastedCoffeeCreate] = []

            for item in payload.details:
                product = self._get_product_or_404(item.product_id)
                line_subtotal = Decimal(item.bag_quantity) * item.unit_value
                line_iva = self._round_money(line_subtotal * IVA_RATE)
                line_total = self._round_money(line_subtotal + line_iva)

                if product.generates_inventory:
                    roasted_details.append(
                        DetailRoastedCoffeeCreate(
                            product_id=product.id,
                            quantity=item.bag_quantity,
                        )
                    )

                details.append(
                    DetailProcess(
                        process=process,
                        date=process_date,
                        product_id=product.id,
                        bag_quantity=item.bag_quantity,
                        grams_per_bag=item.grams_per_bag,
                        unit_value=item.unit_value,
                        iva=line_iva,
                        total=line_total,
                        observations=item.observations,
                    )
                )

            self.db.add_all(details)

            # 3. RoastedCoffee dentro de la misma transacción (sin commit propio)
            if roasted_details:
                roasted_service = RoastedCoffeeService(self.db)
                roasted_service.build_roasted_coffee_in_transaction(
                    process_id=process.id,
                    observations=f"Generado automáticamente desde el proceso #{process.id}",
                    details=roasted_details,
                )

            # 4. Costo unitario de los lotes generados (misma transacción)
            self.db.flush()
            ProcessCostService(self.db).recalculate_process_costs(process.id)

            # 5. COMMIT único: proceso + detalles + roasted coffee + costos
            self.db.commit()

        except SQLAlchemyError as e:
            self.db.rollback()
            print("ERROR SQL:", repr(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating process",
            )

        # ── Bloque 2: ajuste de inventario de pergamino (transacción propia) ──
        # Guardar el id en una variable local: después del commit el objeto
        # process puede quedar expirado por SQLAlchemy y acceder a .id relanzaría
        # una consulta que podría fallar fuera de contexto.
        process_id = process.id
        try:
            parchment_service = ParchmentService(self.db)
            adjustment = ParchmentInventoryAdjustment(
                parchment_id=payload.parchment_id,
                quantity=-payload.parchment_kg,
                reason="Added a new process",
                movement_type="parchment_exit",
                responsible="Persona de prueba",
                observations="Registro de un nuevo proceso, se elimina la cantidad de pergamino utilizada en el proceso",
                process_id=process_id,
            )
            parchment_service.adjust_parchment_inventory(adjustment)
            self.db.commit()

        except HTTPException:
            # Fallo de validación de negocio (ej: stock insuficiente).
            # El proceso ya fue commiteado; solo se hace rollback del ajuste y se relanza.
            self.db.rollback()
            raise

        except SQLAlchemyError as e:
            self.db.rollback()
            print("ERROR SQL:", repr(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Process created but error adjusting parchment inventory",
            )

        return self.get_process_by_id(process_id)


    def update_process(self, process_id: int, payload: ProcessUpdate) -> Process:
        """
        Actualiza proceso y reemplaza sus detalles.
        """
        process = self.db.query(Process).filter(Process.id == process_id).first()
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found",
            )

        process_date = self._parse_process_date(payload.process_date)
        parchment = self._get_parchment_or_404(payload.parchment_id)
        self._validate_parchment_quantity(parchment, payload.parchment_kg)

        resultant_kg, subtotal = self._calculate_totals(payload)
        process_iva = self._round_money(subtotal * IVA_RATE)
        process_total = self._round_money(subtotal + process_iva)
        yield_percentage = self._calculate_yield(resultant_kg, payload.parchment_kg)

        process.invoice_number = payload.invoice_number.strip()
        process.process_date = process_date
        process.parchment_id = payload.parchment_id
        process.parchment_kg = payload.parchment_kg
        process.resultant_kg = resultant_kg
        process.yield_percentage = yield_percentage
        process.subtotal = subtotal
        process.iva = process_iva
        process.total = process_total
        process.observations = payload.observations

        new_details: List[DetailProcess] = []
        for item in payload.details:
            product = self._get_product_or_404(item.product_id)
            line_subtotal = Decimal(item.bag_quantity) * item.unit_value
            line_iva = self._round_money(line_subtotal * IVA_RATE)
            line_total = self._round_money(line_subtotal + line_iva)

            new_details.append(
                DetailProcess(
                    process=process,
                    date=process_date,
                    product_id=product.id,
                    bag_quantity=item.bag_quantity,
                    grams_per_bag=item.grams_per_bag,
                    unit_value=item.unit_value,
                    iva=line_iva,
                    total=line_total,
                    observations=item.observations,
                )
            )

        try:
            process.details.clear()
            self.db.flush()
            process.details.extend(new_details)
            self.db.flush()
            ProcessCostService(self.db).recalculate_process_costs(process.id)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating process",
            )

        return self.get_process_by_id(process.id)


    def delete_process(self, process_id: int) -> bool:
        """
        Elimina un proceso y sus detalles (cascade).

        Si el proceso tiene registros relacionados (ventas, ferias,
        movimientos o gastos de producción sobre sus lotes) se bloquea
        con 409 indicando dónde está relacionado: hay que borrar
        primero esos hijos.
        """
        process = self.db.query(Process).filter(Process.id == process_id).first()
        if not process:
            return False

        self._raise_if_process_has_children(process_id)

        try:
            self.db.delete(process)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting process",
            )
        return True

    def _raise_if_process_has_children(self, process_id: int) -> None:
        """Lanza 409 con el detalle de dónde está relacionado el proceso."""
        drc_ids = [
            row[0]
            for row in self.db.query(DetailRoastedCoffee.id)
            .join(
                RoastedCoffee,
                DetailRoastedCoffee.roasted_coffee_id == RoastedCoffee.id,
            )
            .filter(RoastedCoffee.process_id == process_id)
            .all()
        ]

        relations: List[str] = []

        if drc_ids:
            sale_ids = sorted(
                {
                    row[0]
                    for row in self.db.query(DetailSale.sale_id)
                    .filter(DetailSale.detail_roasted_coffee_id.in_(drc_ids))
                    .all()
                }
            )
            if sale_ids:
                relations.append(
                    f"ventas #{', #'.join(str(s) for s in sale_ids)}"
                )

            fair_names = sorted(
                {
                    row[0]
                    for row in self.db.query(Fair.name)
                    .join(FairInventory, FairInventory.fair_id == Fair.id)
                    .filter(
                        FairInventory.detail_roasted_coffee_id.in_(drc_ids)
                    )
                    .all()
                }
            )
            if fair_names:
                relations.append(f"ferias: {', '.join(fair_names)}")

            movement_count = (
                self.db.query(RoastedMovementDetail)
                .filter(
                    RoastedMovementDetail.detail_roasted_coffee_id.in_(drc_ids)
                )
                .count()
            )
            if movement_count:
                relations.append(
                    f"{movement_count} movimiento(s) de maquilado"
                )

        expense_count = (
            self.db.query(ProcessExpense)
            .filter(ProcessExpense.process_id == process_id)
            .count()
        )
        if expense_count:
            relations.append(f"{expense_count} gasto(s) de producción")

        if relations:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"No se puede eliminar el proceso #{process_id}: "
                    f"está relacionado con {'; '.join(relations)}. "
                    "Para eliminarlo, borra primero esos registros."
                ),
            )


    # def adjust_roasted_inventory(self, adjustment_data: ParchmentInventoryAdjustment) -> dict:
    #     """
    #     Realiza un ajuste manual de inventario de pergamino.

    #     Este método permite:
    #     - Ajustes (correcciones)
    #     - Mermas (pérdidas)
    #     - Devoluciones (entradas)

    #     Args:
    #         adjustment_data (ParchmentInventoryAdjustment): Datos del ajuste.

    #     Returns:
    #         dict: Información del ajuste realizado.

    #     Raises:
    #         HTTPException: Si el pergamino no existe o cantidad insuficiente.
    #     """
        
    #     print("Entro al ajuste")
        
    #     parchment = self.db.query(Parchment).filter(Parchment.id == adjustment_data.parchment_id).first()
    #     raise_if_not_exists(parchment, "Pergamino no encontrado")

    #     # Validar que no se intente sacar más de lo disponible
    #     if adjustment_data.quantity < 0:
    #         if abs(adjustment_data.quantity) > parchment.remaining_quantity:
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail=f"Insufficient quantity. Available: {parchment.remaining_quantity} kg"
    #             )

    #     previous_quantity = parchment.remaining_quantity


    #     # 1. Calcular la diferencia con signo para el historial (ej: 40 - 50 = -10)
    #     difference = Decimal(str(adjustment_data.quantity)) - Decimal(str(previous_quantity))

    #     # 2. Asignar el valor final exacto al inventario
    #     parchment.remaining_quantity = adjustment_data.quantity if adjustment_data.movement_type not in ['parchment_exit'] else previous_quantity - abs(Decimal(str(adjustment_data.quantity)))


    #     # Determinar tipo de movimiento
    #     movement_type_map = {
    #         'adjustment': MovementTypeEnum.adjustment,
    #         'spoilage': MovementTypeEnum.spoilage,
    #         'devolution': MovementTypeEnum.devolution,
    #         'parchment_entrance': MovementTypeEnum.parchment_entrance,
    #         'parchment_exit': MovementTypeEnum.parchment_exit
    #     }

    #     # Crear movimiento
    #     movement = InventoryMovement(
    #         movement_date=datetime.now(),
    #         movement_type=movement_type_map[adjustment_data.movement_type],
    #         product_type=ProductMovementTypeEnum.parchment,
    #         parchment_id=parchment.id,
    #         quantity=adjustment_data.quantity if adjustment_data.movement_type in ['parchment_exit'] else difference,
    #         reason=adjustment_data.reason,
    #         responsible=adjustment_data.responsible,
    #         observations=adjustment_data.observations,
    #         processes_id=None,
    #     )

    #     self.db.add(movement)
    #     self.db.flush()  # flush en lugar de commit para que el llamador controle la transacción

    #     return {
    #         "parchment_id": parchment.id,
    #         "previous_quantity": previous_quantity,
    #         "adjustment_quantity": adjustment_data.quantity,
    #         "new_quantity": parchment.remaining_quantity,
    #         "movement_id": movement.id,
    #         "message": "Inventory adjustment completed successfully"
    #     }


    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_process_date(raw_date: str):
        try:
            return datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="process_date must be in YYYY-MM-DD format",
            )

    def _get_parchment_or_404(self, parchment_id: int) -> Parchment:
        parchment = self.db.query(Parchment).filter(Parchment.id == parchment_id).first()
        if not parchment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parchment not found",
            )
        return parchment

    def _get_product_or_404(self, product_id: int) -> Product:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        return product

    @staticmethod
    def _validate_parchment_quantity(parchment: Parchment, requested_kg: Decimal) -> None:
        if requested_kg > parchment.remaining_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough dry parchment inventory",
            )

    @staticmethod
    def _calculate_yield(resultant_kg: Decimal, parchment_kg: Decimal) -> Decimal:
        return (
            Decimal("0")
            if parchment_kg == 0
            else ProcessService._round_kg((resultant_kg / parchment_kg) * Decimal("100"))
        )

    @staticmethod
    def _calculate_totals(payload: ProcessCreate) -> tuple[Decimal, Decimal]:
        resultant_kg = Decimal("0")
        subtotal = Decimal("0")
        for item in payload.details:
            resultant_kg += (Decimal(item.bag_quantity) * Decimal(item.grams_per_bag)) / Decimal("1000")
            subtotal += Decimal(item.bag_quantity) * item.unit_value
        return ProcessService._round_kg(resultant_kg), ProcessService._round_money(subtotal)

    @staticmethod
    def _round_money(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _round_kg(value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.001"))