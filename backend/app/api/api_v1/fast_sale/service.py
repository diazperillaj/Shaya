from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List
from fastapi import HTTPException, status

# Ajusta las rutas de importación según la estructura de tu proyecto
from app.models.fast_sale import FastSale
from app.api.api_v1.fast_sale.schema import FastSaleCreate, FastSaleUpdate

def raise_if_exists(query, detail: str):
    """
    Valida la existencia previa de un registro en la base de datos.
    """
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class FastSaleService:
    """
    Servicio encargado de la lógica de negocio relacionada con las ventas rápidas.

    Separa la lógica de persistencia de los endpoints HTTP.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con una sesión de base de datos.

        Args:
            db (Session): Sesión activa de SQLAlchemy.
        """
        self.db = db

    def get_fast_sales(self) -> List[FastSale]:
        """
        Obtiene la lista de ventas rápidas registradas.

        Ordena los resultados por ID descendente (últimos primero).

        Returns:
            List[FastSale]: Lista de ventas rápidas.
        """
        return (
            self.db
            .query(FastSale)
            .order_by(desc(FastSale.id))
            .all()
        )

    def get_fast_sale_by_id(self, fast_sale_id: int) -> FastSale:
        """
        Obtiene una venta rápida a partir de su identificador único.

        Args:
            fast_sale_id (int): ID de la venta rápida.

        Returns:
            FastSale | None: Venta encontrada o None si no existe.
        """
        return self.db.query(FastSale).filter(FastSale.id == fast_sale_id).first()

    def create_fast_sale(self, fast_sale_data: FastSaleCreate) -> FastSale:
        """
        Crea una nueva venta rápida en el sistema.

        Args:
            fast_sale_data (FastSaleCreate): Datos de la venta a crear.

        Returns:
            FastSale: Venta creada exitosamente.
        """
        fast_sale = FastSale(
            product_id=fast_sale_data.product_id,
            quantity=fast_sale_data.quantity,
            price=fast_sale_data.price,
            user_id=fast_sale_data.user_id,
            description=fast_sale_data.description
        )

        self.db.add(fast_sale)
        self.db.commit()
        self.db.refresh(fast_sale)
        return fast_sale

    def update_fast_sale(self, fast_sale_id: int, fast_sale_data: FastSaleUpdate) -> FastSale:
        """
        Actualiza la información de una venta rápida existente.

        Permite actualización parcial de datos.

        Args:
            fast_sale_id (int): ID de la venta.
            fast_sale_data (FastSaleUpdate): Datos a modificar.

        Returns:
            FastSale | None: Venta actualizada o None si no existe.
        """
        fast_sale = self.db.query(FastSale).filter(FastSale.id == fast_sale_id).first()

        if not fast_sale:
            return None

        if fast_sale_data.product_id is not None:
            fast_sale.product_id = fast_sale_data.product_id

        if fast_sale_data.quantity is not None:
            fast_sale.quantity = fast_sale_data.quantity

        if fast_sale_data.price is not None:
            fast_sale.price = fast_sale_data.price

        if fast_sale_data.user_id is not None:
            fast_sale.user_id = fast_sale_data.user_id

        if fast_sale_data.description is not None:
            fast_sale.description = fast_sale_data.description

        self.db.commit()
        self.db.refresh(fast_sale)
        return fast_sale

    def delete_fast_sale(self, fast_sale_id: int) -> bool:
        """
        Elimina la venta rápida por su identificador único.

        Args:
            fast_sale_id (int): Identificador único.

        Returns:
            bool: True si se eliminó, False si no lo logró.
        """
        fast_sale = self.db.query(FastSale).filter(FastSale.id == fast_sale_id).first()

        if not fast_sale:
            return False

        self.db.delete(fast_sale)
        self.db.commit()

        return True

    def get_fast_sales_filtered(self, search: str = None) -> List[FastSale]:
        """
        Obtiene ventas rápidas aplicando filtros opcionales.

        Permite buscar por:
        - Descripción

        Args:
            search (str, opcional): Texto de búsqueda.

        Returns:
            List[FastSale]: Ventas que cumplen los criterios.
        """
        query = self.db.query(FastSale)

        if search:
            query = query.filter(
                FastSale.description.ilike(f"%{search}%")
            )

        return query.order_by(desc(FastSale.id)).all()