// src/features/Inventory/types.ts

/**
 * Representa un registro de inventario en el frontend.
 *
 * Este modelo se utiliza para:
 * - Mostrar información en tablas y formularios
 * - Enviar datos a la API al crear o actualizar inventario
 *
 * Es un modelo plano, desacoplado de la estructura del backend.
 */
export interface Inventory {

  /** Identificador único del inventario */
  id: number

  /** Información del lote de pergamino */
  parchment_info: string

  /** Tipo de producto (ej: Ground Coffee, Coffee Beans) */
  type: string

  /** Cantidad del producto */
  amount: number

  /** Variedad del café */
  variety: string

  /** Nivel de tostión */
  roast_level: string

  /** Precio por unidad */
  unity_price: number

  /** Precio total */
  total_price: number
}

/**
 * Filtros disponibles para la consulta de inventario.
 */
export interface InventorysQuery {

  /** Texto de búsqueda (lote, tipo, variedad, etc.) */
  search?: string
}

/**
 * Representa la estructura del inventario
 * tal como la envía la API.
 *
 * Este tipo refleja fielmente el contrato del backend
 * y debe usarse únicamente en servicios y mappers.
 */
export interface InventoryApiResponse {

  /** Identificador único */
  id: number

  /** Información del lote de pergamino */
  parchment_info: string

  /** Tipo de producto */
  type: string

  /** Cantidad */
  amount: number

  /** Variedad */
  variety: string

  /** Nivel de tostión */
  roast_level: string

  /** Precio por unidad */
  unity_price: number

  /** Precio total */
  total_price: number
}