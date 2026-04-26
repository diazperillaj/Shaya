from pydantic import BaseModel, EmailStr, Field, field_validator, StringConstraints
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from typing_extensions import Annotated
from app.schemas.inventory import InventoryResponse
from app.api.api_v1.farmers.schema import FarmerResponse
from typing import List

ValidationLength = Annotated[
    str,
    StringConstraints(min_length=2),
]


# ============================================================================
# PARCHMENT SCHEMAS
# ============================================================================

class ParchmentCreate(BaseModel):
    """
    Modelo utilizado para la creación de inventario de café pergamino.
    
    Contiene las validaciones necesarias para registrar una compra de
    café pergamino a un caficultor.
    """
    
    farmer_id: int = Field(..., gt=0, description="ID del caficultor vendedor")
    product_id: int = Field(..., gt=0, description="ID del producto en catálogo")
    variety: Optional[ValidationLength] = Field(None, max_length=100, description="Variedad del café")
    altitude: Optional[Decimal] = Field(None, ge=0, le=9999.99, description="Altitud en metros")
    humidity: Optional[Decimal] = Field(None, ge=0, le=100, description="Porcentaje de humedad")
    full_price: Decimal = Field(..., gt=0, description="Precio de compra por kg")
    initial_quantity: Decimal = Field(..., gt=0, description="Cantidad en kg")
    purchase_date: date = Field(..., description="Fecha de compra del pergamino")
    origin_batch: Optional[str] = Field(None, max_length=100, description="Lote del caficultor")
    observations: Optional[str] = None
    
    @field_validator('purchase_date')
    @classmethod
    def validate_date_not_future(cls, v: date) -> date:
        """Valida que la fecha de compra no sea futura"""
        if v > date.today():
            raise ValueError('Purchase date cannot be in the future')
        return v
    
    @field_validator('altitude')
    @classmethod
    def validate_altitude(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Valida rango razonable de altitud para cultivo de café"""
        if v is not None and v > 0:
            if v < 800 or v > 2500:
                raise ValueError('Coffee altitude typically ranges between 800m and 2500m')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "farmer_id": 1,
                "product_id": 1,
                "variety": "Caturra",
                "altitude": 1800.00,
                "humidity": 10.5,
                "purchase_price": 8500.00,
                "initial_quantity": 100.500,
                "purchase_date": "2024-03-15",
                "origin_batch": "BATCH-JUAN-2024-001",
                "observations": "High quality coffee from spring harvest"
            }
        }


class ParchmentResponse(BaseModel):
    """
    Modelo de respuesta para endpoints que devuelven información completa
    de un pergamino.
    """
    
    id: int
    inventory: InventoryResponse
    farmer: FarmerResponse
    variety: Optional[str]
    altitude: Optional[Decimal]
    humidity: Optional[Decimal]
    purchase_price: Decimal
    full_price: Decimal
    initial_quantity: Decimal
    remaining_quantity: Decimal
    purchase_date: date
    origin_batch: Optional[str]
    
    class Config:
        from_attributes = True


class ParchmentDetailResponse(BaseModel):
    """
    Modelo de respuesta detallado que incluye información del caficultor
    y cálculos adicionales.
    """
    
    id: int
    inventory: InventoryResponse
    variety: Optional[str]
    altitude: Optional[Decimal]
    humidity: Optional[Decimal]
    purchase_price: Decimal
    full_price: Decimal
    initial_quantity: Decimal
    remaining_quantity: Decimal
    purchase_date: date
    origin_batch: Optional[str]
    
    # Información del caficultor
    farmer: FarmerResponse
    
    # Cálculos derivados
    used_quantity: Decimal
    used_percentage: Decimal
    remaining_inventory_value: Decimal
    total_purchase_value: Decimal
    
    class Config:
        from_attributes = True


class ParchmentUpdate(BaseModel):
    """
    Modelo utilizado para la actualización parcial de un pergamino.
    
    Todos los campos son opcionales, permitiendo actualizaciones parciales.
    Solo permite actualizar datos descriptivos, no cantidades
    (las cantidades se manejan por movimientos).
    """
    
    farmer_id: Optional[int] = Field(None, gt=0, description="ID del nuevo caficultor vendedor")
    
    variety: Optional[ValidationLength] = Field(None, max_length=100)
    altitude: Optional[Decimal] = Field(None, ge=0, le=9999.99)
    humidity: Optional[Decimal] = Field(None, ge=0, le=100)
    origin_batch: Optional[str] = Field(None, max_length=100)
    remaining_quantity: Optional[Decimal] = Field(None, ge=0, le=9999.99)
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    full_price: Optional[Decimal] = Field(None, ge=0)
    observations: Optional[str] = None
    purchase_date: Optional[date] = None
    
    @field_validator('altitude')
    @classmethod
    def validate_altitude(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Valida rango razonable de altitud para cultivo de café"""
        if v is not None and v > 0:
            if v < 800 or v > 2500:
                raise ValueError('Coffee altitude typically ranges between 800m and 2500m')
        return v


class ParchmentUpdateResponse(BaseModel):
    """
    Modelo de respuesta después de una actualización de pergamino.
    """
    
    id: int
    inventory: InventoryResponse
    farmer: FarmerResponse
    variety: Optional[str]
    altitude: Optional[Decimal]
    humidity: Optional[Decimal]
    purchase_price: Decimal
    full_price: Decimal
    initial_quantity: Decimal
    remaining_quantity: Decimal
    purchase_date: date
    origin_batch: Optional[str]
    
    class Config:
        from_attributes = True


class ParchmentInventoryAdjustment(BaseModel):
    """
    Modelo para realizar ajustes manuales de inventario de pergamino.
    
    Usado para mermas, pérdidas, devoluciones o correcciones.
    """
    
    parchment_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., description="Cantidad a ajustar (positivo=entrada, negativo=salida)")
    reason: ValidationLength = Field(..., max_length=255, description="Motivo del ajuste")
    movement_type: str = Field(..., description="Tipo: 'adjustment', 'spoilage', 'devolution'")
    responsible: Optional[str] = Field(None, max_length=255)
    observations: Optional[str] = None
    
    @field_validator('movement_type')
    @classmethod
    def validate_movement_type(cls, v: str) -> str:
        """Valida que el tipo de movimiento sea válido"""
        allowed_types = ['adjustment', 'spoilage', 'devolution']
        if v not in allowed_types:
            raise ValueError(f'Movement type must be one of: {", ".join(allowed_types)}')
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity_not_zero(cls, v: Decimal) -> Decimal:
        """Valida que la cantidad no sea cero"""
        if v == 0:
            raise ValueError('Quantity cannot be zero')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "parchment_id": 1,
                "quantity": -5.5,
                "reason": "Moisture damage",
                "movement_type": "spoilage",
                "responsible": "Carlos Pérez",
                "observations": "2 bags damaged due to water leakage"
            }
        }


class ParchmentAdjustmentResponse(BaseModel):
    """
    Modelo de respuesta después de realizar un ajuste de inventario.
    """
    
    parchment_id: int
    previous_quantity: Decimal
    adjustment_quantity: Decimal
    new_quantity: Decimal
    movement_id: int
    message: str
    
    class Config:
        from_attributes = True


class ParchmentListItem(BaseModel):
    """
    Modelo simplificado para listado de pergaminos.
    """
    
    id: int
    farmer_name: str
    variety: Optional[str]
    purchase_date: date
    initial_quantity: Decimal
    remaining_quantity: Decimal
    purchase_price: Decimal
    remaining_value: Decimal
    origin_batch: Optional[str]
    
    class Config:
        from_attributes = True


class ParchmentListResponse(BaseModel):
    """
    Modelo de respuesta para listar pergaminos con paginación.
    """
    
    items: List[ParchmentListItem]
    total: int
    page: int
    size: int
    pages: int
    
    class Config:
        from_attributes = True


class ParchmentInventorySummary(BaseModel):
    """
    Modelo de respuesta para el resumen general del inventario de pergamino.
    """
    
    total_parchments: int
    total_kg_available: Decimal
    total_kg_used: Decimal
    total_inventory_value: Decimal
    average_purchase_price: Decimal
    
    class Config:
        from_attributes = True


class MovementHistoryItem(BaseModel):
    """
    Modelo para un item del historial de movimientos.
    """
    
    id: int
    movement_date: datetime
    movement_type: str
    quantity: Decimal
    reason: Optional[str]
    responsible: Optional[str]
    observations: Optional[str]
    
    class Config:
        from_attributes = True


class ParchmentMovementHistory(BaseModel):
    """
    Modelo de respuesta para el historial de movimientos de un pergamino.
    """
    
    parchment_id: int
    parchment_info: ParchmentResponse
    movements: List[MovementHistoryItem]
    
    class Config:
        from_attributes = True
