// src/features/Inventory/types.ts

import type { Farmer } from "../../farmers/models/types"

interface ProductType {
  id: number
  name: string
}

interface InventoryType {
  id: number
  product: ProductType
  quantity: string
  observations: string
  date: string
}

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

  product: ProductType

  farmer: Farmer

  /** Variedad del café */
  variety: string

  /** Altitud del lote (msnm) */
  elevation: number

  /** Humedad del lote (%) */
  humidity: number

  /** Precio de compra */
  price: number
  
  /** Precio por carga */
  full_price: number

  /** Cantidad inicial del lote */
  quantity: number

  /** Stock actual disponible */
  remaining_quantity: number

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
  id: number

  inventory: InventoryType

  farmer: Farmer

  variety: string
  altitude: string
  humidity: string
  purchase_price: string
  full_price: string
  initial_quantity: string
  remaining_quantity: string
  purchase_date: string
}