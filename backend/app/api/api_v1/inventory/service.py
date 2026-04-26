from app.models.product import Product
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, func
from app.models.parchment import Parchment
from app.models.farmer import Farmer
from app.models.person import Person
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement, MovementTypeEnum, ProductMovementTypeEnum
from app.api.api_v1.inventory.schema import (
    ParchmentCreate,
    ParchmentResponse, 
    ParchmentUpdate, 
    ParchmentInventoryAdjustment,
)
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

# Manejo de excepciones
from fastapi import HTTPException, status


def raise_if_exists(query, detail: str):
    """
    Valida la existencia previa de un registro en la base de datos.

    Args:
        query: Consulta SQLAlchemy que será evaluada.
        detail (str): Mensaje de error a devolver si el registro existe.

    Raises:
        HTTPException: Si la consulta retorna un resultado.
    """
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


def raise_if_not_exists(obj, detail: str):
    """
    Valida que un objeto exista en la base de datos.

    Args:
        obj: Objeto a validar.
        detail (str): Mensaje de error si no existe.

    Raises:
        HTTPException: Si el objeto es None.
    """
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

def calculate_purchase_price(total_price: Decimal, quantity: Decimal) -> Decimal:
    """
    Calcula el precio unitario de compra a partir del precio total y la cantidad.

    Args:
        total_price (Decimal): Precio total pagado por el pergamino.
        quantity (Decimal): Cantidad de pergamino en kilogramos.

    Returns:
        Decimal: Precio unitario de compra por kilogramo.

    Raises:
        ValueError: Si la cantidad es cero o negativa.
    """
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero to calculate purchase price.")
    
    return (quantity * total_price) / 125


def format_name(name: str) -> str:
    """
    Normaliza nombres propios respetando preposiciones y conectores.

    Convierte cada palabra a mayúscula inicial, excepto:
    'de', 'del', 'la', 'las', 'los', 'y'.

    Ejemplo:
        Entrada:  "maria de las mercedes"
        Salida:   "Maria de las Mercedes"

    Args:
        name (str): Nombre completo a formatear.

    Returns:
        str: Nombre formateado.
    """
    exceptions = {'de', 'del', 'la', 'las', 'los', 'y'}
    return ' '.join(
        word.capitalize() if word.lower() not in exceptions else word.lower()
        for word in name.split()
    )


class ParchmentService:
    """
    Servicio encargado de la lógica de negocio relacionada con el inventario de café pergamino.

    Separa la lógica de persistencia de los endpoints HTTP.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
        """
        self.db = db

    def get_parchments(self) -> List[ParchmentResponse]:
        """
        Obtiene la lista de pergaminos registrados.

        Incluye la información del inventario y caficultor asociados.

        Returns:
            List[Parchment]: Lista de pergaminos.
        """
        
        db = (self.db
            .query(Parchment)
            .options(
                joinedload(Parchment.farmer).joinedload(Farmer.person),
                joinedload(Parchment.inventory)
            )
            .order_by(desc(Parchment.id))
            .all())
        
        return db

    def get_parchment_by_id(self, parchment_id: int) -> Parchment:
        """
        Obtiene un pergamino a partir de su identificador único.

        Args:
            parchment_id (int): ID del pergamino.

        Returns:
            Parchment: Pergamino encontrado.

        Raises:
            HTTPException: Si el pergamino no existe.
        """
        parchment = (
            self.db.query(Parchment)
            .options(
                joinedload(Parchment.farmer).joinedload(Farmer.person),
                joinedload(Parchment.inventory)
            )
            .filter(Parchment.id == parchment_id)
            .first()
        )
        raise_if_not_exists(parchment, "Parchment not found")
        return parchment

    def create_parchment(self, parchment_data: ParchmentCreate) -> Parchment:
        """
        Crea un nuevo registro de café pergamino en el inventario.

        Este método realiza:
        1. Valida que existan el caficultor y el producto
        2. Crea el registro base en Inventory
        3. Crea el registro detallado en Parchment
        4. Crea automáticamente un movimiento de entrada en InventoryMovement

        Args:
            parchment_data (ParchmentCreate): Datos del pergamino a crear.

        Returns:
            Parchment: Pergamino creado exitosamente.

        Raises:
            HTTPException: Si el caficultor o producto no existen.
        """
        # Validar que existe el caficultor
        farmer = self.db.query(Farmer).filter(Farmer.id == parchment_data.farmer_id).first()
        raise_if_not_exists(farmer, "Farmer not found")

        # Crear registro base de inventario
        
        product = self.db.query(Product).filter(Product.type == "other").first()
        
        inventory = Inventory(
            product_id=product.id,
            date=datetime.now(),
            quantity=parchment_data.initial_quantity,
            observations=parchment_data.observations
        )

        # Crear registro de pergamino
        parchment = Parchment(
            inventory=inventory,
            farmer_id=parchment_data.farmer_id,
            variety=parchment_data.variety,
            altitude=parchment_data.altitude,
            humidity=parchment_data.humidity,
            purchase_price=calculate_purchase_price(parchment_data.full_price, parchment_data.initial_quantity),
            full_price=parchment_data.full_price,
            initial_quantity=parchment_data.initial_quantity,
            remaining_quantity=parchment_data.initial_quantity,
            purchase_date=parchment_data.purchase_date,
            origin_batch=parchment_data.origin_batch
        )

        self.db.add(parchment)
        self.db.flush()  # Para obtener el ID antes del commit

        # Crear movimiento de entrada automáticamente
        movement = InventoryMovement(
            movement_date=datetime.now(),
            movement_type=MovementTypeEnum.parchment_entrance,
            product_type=ProductMovementTypeEnum.parchment,
            parchment_id=parchment.id,
            quantity=parchment_data.initial_quantity,
            reason="Initial parchment purchase",
            observations=f"Purchase from farmer {farmer.person.full_name} - Batch: {parchment_data.origin_batch or 'N/A'}"
        )

        self.db.add(movement)
        self.db.commit()
        self.db.refresh(parchment)
        
        return parchment

    def delete_parchment(self, parchment_id: int) -> bool:
        """
        Elimina un pergamino por su identificador único.

        Solo se puede eliminar si no tiene movimientos asociados
        o productos maquilados derivados.

        Args:
            parchment_id (int): Identificador único.

        Returns:
            Boolean: True si se eliminó, False si no existe.

        Raises:
            HTTPException: Si tiene movimientos o productos derivados.
        """
        parchment = self.db.query(Parchment).filter(Parchment.id == parchment_id).first()

        if not parchment:
            return False

        # Verificar si tiene productos maquilados derivados
        if parchment.processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete parchment with processed products"
            )

        # Eliminar el inventario asociado (cascada elimina parchment y movimientos)
        if parchment.inventory:
            self.db.delete(parchment.inventory)

        self.db.commit()
        return True

    def adjust_parchment_inventory(self, adjustment_data: ParchmentInventoryAdjustment) -> dict:
        """
        Realiza un ajuste manual de inventario de pergamino.

        Este método permite:
        - Ajustes (correcciones)
        - Mermas (pérdidas)
        - Devoluciones (entradas)

        Args:
            adjustment_data (ParchmentInventoryAdjustment): Datos del ajuste.

        Returns:
            dict: Información del ajuste realizado.

        Raises:
            HTTPException: Si el pergamino no existe o cantidad insuficiente.
        """
        
        print("Entro al ajuste")
        
        parchment = self.db.query(Parchment).filter(Parchment.id == adjustment_data.parchment_id).first()
        raise_if_not_exists(parchment, "Pergamino no encontrado")

        # Validar que no se intente sacar más de lo disponible
        if adjustment_data.quantity < 0:
            if abs(adjustment_data.quantity) > parchment.remaining_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient quantity. Available: {parchment.remaining_quantity} kg"
                )

        previous_quantity = parchment.remaining_quantity

        # 1. Calcular la diferencia con signo para el historial (ej: 40 - 50 = -10)
        difference = Decimal(str(adjustment_data.quantity)) - Decimal(str(previous_quantity))

        # 2. Asignar el valor final exacto al inventario
        parchment.remaining_quantity = adjustment_data.quantity

        # Determinar tipo de movimiento
        movement_type_map = {
            'adjustment': MovementTypeEnum.adjustment,
            'spoilage': MovementTypeEnum.spoilage,
            'devolution': MovementTypeEnum.devolution
        }

        # Crear movimiento
        movement = InventoryMovement(
            movement_date=datetime.now(),
            movement_type=movement_type_map[adjustment_data.movement_type],
            product_type=ProductMovementTypeEnum.parchment,
            parchment_id=parchment.id,
            quantity=difference,
            reason=adjustment_data.reason,
            responsible=adjustment_data.responsible,
            observations=adjustment_data.observations
        )

        self.db.add(movement)
        self.db.flush()  # flush en lugar de commit para que el llamador controle la transacción

        return {
            "parchment_id": parchment.id,
            "previous_quantity": previous_quantity,
            "adjustment_quantity": adjustment_data.quantity,
            "new_quantity": parchment.remaining_quantity,
            "movement_id": movement.id,
            "message": "Inventory adjustment completed successfully"
        }

    def update_parchment(self, parchment_id: int, parchment_data: ParchmentUpdate) -> Parchment:
        """
        Actualiza la información de un pergamino existente.

        Permite actualización parcial de datos descriptivos.
        Si la cantidad restante es modificada, se crea automáticamente un movimiento de inventario.

        Args:
            parchment_id (int): ID del pergamino.
            parchment_data (ParchmentUpdate): Datos a modificar.

        Returns:
            Parchment: Pergamino actualizado.

        Raises:
            HTTPException: Si el pergamino no existe.
        """
        
        
        
        parchment = self.db.query(Parchment).filter(Parchment.id == parchment_id).first()
        raise_if_not_exists(parchment, "Parchment not found")

        # Obtener solo los campos enviados en la petición
        update_data = (
            parchment_data.model_dump(exclude_unset=True)
            if hasattr(parchment_data, 'model_dump')
            else parchment_data.dict(exclude_unset=True)
        )
        
        if 'variety' in update_data:
            parchment.variety = update_data['variety']
            
        if 'observations' in update_data or 'purchase_date' in update_data:
            inventory = self.db.query(Inventory).filter(Inventory.id == parchment.inventory_id).first()
            if inventory:
                if 'observations' in update_data:
                    inventory.observations = update_data['observations']
                    
                if 'purchase_date' in update_data:
                    inventory.date = update_data['purchase_date']
                    parchment.purchase_date = update_data['purchase_date']

        if 'altitude' in update_data:
            parchment.altitude = update_data['altitude']

        if 'humidity' in update_data:
            parchment.humidity = update_data['humidity']

        if 'full_price' in update_data:
            parchment.full_price = update_data['full_price']
            parchment.purchase_price = calculate_purchase_price(update_data['full_price'], parchment.initial_quantity)
            
        if 'origin_batch' in update_data:
            parchment.origin_batch = update_data['origin_batch']

        if 'farmer_id' in update_data:
            new_farmer = self.db.query(Farmer).filter(Farmer.id == update_data['farmer_id']).first()
            raise_if_not_exists(new_farmer, "New farmer not found")
            parchment.farmer_id = update_data['farmer_id']

        # Verificar si initial_quantity fue enviado y es diferente al actual        
        if 'remaining_quantity' in update_data:
            incoming = Decimal(str(update_data['remaining_quantity']))
            current = Decimal(str(parchment.remaining_quantity))
            
            print(f"Prueba1: incoming={incoming}, current={current}")

            if incoming != current:
                adjustment_data = ParchmentInventoryAdjustment(
                    parchment_id=parchment.id,
                    quantity=incoming,
                    reason="Actualización manual desde la edición del pergamino",
                    movement_type="adjustment",
                    responsible="Sistema"
                )
                
                
                # adjust_parchment_inventory ahora hace flush, no commit
                self.adjust_parchment_inventory(adjustment_data)

        # Un solo commit al final que persiste todo (campos descriptivos + ajuste si hubo)
        self.db.commit()
        self.db.refresh(parchment)
        return parchment

    def get_parchments_filtered(
        self, 
        search: Optional[str] = None,
        farmer_id: Optional[int] = None,
        variety: Optional[str] = None,
        min_quantity: Optional[Decimal] = None
    ) -> List[Parchment]:
        """
        Obtiene pergaminos aplicando filtros opcionales.

        Permite buscar por:
        - Nombre del caficultor
        - Variedad de café
        - Lote de origen
        - ID de caficultor específico
        - Cantidad mínima disponible

        Args:
            search (str, opcional): Texto de búsqueda.
            farmer_id (int, opcional): Filtrar por caficultor.
            variety (str, opcional): Filtrar por variedad.
            min_quantity (Decimal, opcional): Cantidad mínima disponible.

        Returns:
            List[Parchment]: Pergaminos que cumplen los criterios.
        """
        query = (
            self.db.query(Parchment)
            .options(
                joinedload(Parchment.farmer).joinedload(Farmer.person),
                joinedload(Parchment.inventory)
            )
        )

        if search:
            query = query.join(Parchment.farmer).join(Farmer.person).filter(
                or_(
                    Person.full_name.ilike(f"%{search}%"),
                    Parchment.variety.ilike(f"%{search}%"),
                    Parchment.origin_batch.ilike(f"%{search}%")
                )
            )

        if farmer_id:
            query = query.filter(Parchment.farmer_id == farmer_id)

        if variety:
            query = query.filter(Parchment.variety.ilike(f"%{variety}%"))

        if min_quantity is not None:
            query = query.filter(Parchment.remaining_quantity >= min_quantity)

        return query.order_by(desc(Parchment.purchase_date)).all()

    def get_parchment_movement_history(self, parchment_id: int) -> dict:
        """
        Obtiene el historial completo de movimientos de un pergamino.

        Args:
            parchment_id (int): ID del pergamino.

        Returns:
            dict: Información del pergamino y sus movimientos.

        Raises:
            HTTPException: Si el pergamino no existe.
        """
        parchment = self.get_parchment_by_id(parchment_id)

        movements = (
            self.db.query(InventoryMovement)
            .filter(InventoryMovement.parchment_id == parchment_id)
            .order_by(InventoryMovement.movement_date.asc())
            .all()
        )

        return {
            "parchment_id": parchment.id,
            "parchment_info": parchment,
            "movements": movements
        }

    def get_inventory_summary(self) -> dict:
        """
        Obtiene un resumen general del inventario de pergamino.

        Returns:
            dict: Estadísticas del inventario.
        """
        total_parchments = self.db.query(Parchment).count()

        total_kg_available = self.db.query(
            func.sum(Parchment.remaining_quantity)
        ).scalar() or Decimal(0)

        total_kg_used = self.db.query(
            func.sum(Parchment.initial_quantity - Parchment.remaining_quantity)
        ).scalar() or Decimal(0)

        total_inventory_value = self.db.query(
            func.sum(Parchment.remaining_quantity * Parchment.purchase_price)
        ).scalar() or Decimal(0)

        avg_purchase_price = self.db.query(
            func.avg(Parchment.purchase_price)
        ).scalar() or Decimal(0)

        return {
            "total_parchments": total_parchments,
            "total_kg_available": total_kg_available,
            "total_kg_used": total_kg_used,
            "total_inventory_value": total_inventory_value,
            "average_purchase_price": avg_purchase_price
        }