// src/features/products/types.ts

/**
 * Representa un producto en el frontend.
 *
 * Este modelo se utiliza para:
 * - Mostrar información en tablas y formularios
 * - Enviar datos a la API al crear o actualizar productos
 *
 * Es un modelo plano, alineado con la estructura del backend.
 */
export interface Product {
  /** Identificador único del producto */
  id: number

  /** Nombre del producto */
  name: string

  /** Cantidad disponible del producto */
  quantity: number

  /** Tipo de producto */
  type: 'parchment' | 'processed' | 'other'

  /** Descripción adicional del producto */
  description?: string
}

/**
 * Filtros disponibles para la consulta de productos.
 *
 * Se utilizan al solicitar la lista de productos
 * desde la API.
 */
export interface ProductsQuery {
  /** Texto de búsqueda (nombre, tipo, descripción, etc.) */
  search?: string
  
  /** Filtro opcional por tipo de producto */
  type?: 'parchment' | 'processed' | 'other'
}

/**
 * Representa la estructura del producto
 * tal como la envía la API.
 *
 * Este tipo refleja fielmente el contrato del backend (Pydantic)
 * y debe usarse únicamente en servicios y mappers.
 */
export interface ProductApiResponse {
  /** Identificador único */
  id: number

  /** Nombre del producto */
  name: string

  /** Cantidad del producto */
  quantity: number

  /** Tipo de producto */
  type: 'parchment' | 'processed' | 'other'

  /** Descripción del producto (puede ser nula desde el backend) */
  description: string | null
}