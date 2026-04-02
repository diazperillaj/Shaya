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

  /** Identificador único del lote */
  id: number

  /** Producto (ej: Café verde, tostado, etc.) */
  product: string

  /** Nombre del caficultor */
  farmer: string

  /** Variedad del café */
  variety: string

  /** Altitud del lote (msnm) */
  elevation: number

  /** Humedad del lote (%) */
  humidity: number

  /** Factor de rendimiento del lote */
  yield_factor: number

  /** Precio de compra */
  price: number
  
  /** Precio por carga */
  full_price: number

  /** Cantidad inicial del lote */
  quantity: number

  /** Stock actual disponible */
  stock: number

  /** Fecha de compra */
  date: string

  /** Observaciones adicionales */
  observation?: string
}

/**
 * Filtros disponibles para la consulta de inventario.
 *
 * Se utilizan al solicitar la lista de inventario
 * desde la API.
 */
export interface InventorysQuery {

  /** Texto de búsqueda (producto, caficultor, variedad, etc.) */
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

  /** Producto */
  product: string

  /** Caficultor */
  farmer: string

  /** Variedad */
  variety: string

  /** Altitud */
  elevation: number

  /** Humedad */
  humidity: number

  /** Factor de rendimiento */
  yield_factor: number

  /** Precio de compra */
  price: number

  /** Precio por carga */
  full_price: number

  /** Cantidad inicial */
  quantity: number

  /** Stock actual */
  stock: number

  /** Fecha de compra */
  date: string

  /** Observaciones */
  observation?: string | null
}