"""
Salida del pergamino seco al inventario (modelo-datos §6.4, decisión C1).

El café propio entra a `parchments` por el mismo flujo de compra que el café
comprado: el servicio del inventario crea el `Inventory`, el `Parchment` y
su movimiento de entrada, y calcula `purchase_price` con la regla de 3 sobre
el `full_price` (precio por carga de 125 kg) que asigna el productor. Aquí
solo se arman sus datos desde el secado.

El servicio del inventario confirma la transacción: lo que el secado haya
cambiado en la misma sesión (su cierre) queda confirmado junto con el
pergamino, o no queda nada si algo falla.
"""

from datetime import date
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.api_v1.inventory.schema import ParchmentCreate
from app.api.api_v1.inventory.service import ParchmentService
from app.core.exceptions.domain import ConflictError
from app.farm_operations.models import Drying
from app.farm_operations.services.traceability import dominant_variety
from app.models.parchment import Parchment
from app.models.product import Product

# Rango de altitud que acepta el inventario para el café pergamino
INVENTORY_ALTITUDE = (Decimal(800), Decimal(2500))


def send_to_inventory(db: Session, drying: Drying, full_price: Decimal, purchase_date: date) -> Parchment:
    """
    Registra el pergamino del secado en el inventario y confirma la
    transacción. Si falla, deshace también los cambios pendientes del secado.
    """
    try:
        # El servicio del inventario usa este producto para todo pergamino
        product = db.query(Product).filter(Product.type == "other").first()
        if product is None:
            raise ConflictError("No hay un producto configurado para registrar pergamino en el inventario")

        farm = drying.farm
        altitude = farm.altitude
        if altitude is not None and not INVENTORY_ALTITUDE[0] <= altitude <= INVENTORY_ALTITUDE[1]:
            altitude = None  # fuera del rango del café, el inventario no la acepta
        variety = dominant_variety(drying)

        try:
            data = ParchmentCreate(
                farmer_id=farm.farmer_id,
                product_id=product.id,
                variety=variety if variety and len(variety.strip()) >= 2 else None,
                altitude=altitude,
                humidity=drying.final_humidity_pct,
                full_price=full_price,
                initial_quantity=drying.output_kg,
                purchase_date=purchase_date,
                observations=f"Producción propia · finca {farm.name} · secado {drying.id}",
                drying_id=drying.id,
            )
        except ValidationError as error:
            raise ConflictError(f"El inventario no acepta estos datos: {error.errors()[0]['msg']}")

        return ParchmentService(db).create_parchment(data)
    except Exception:
        db.rollback()
        raise
