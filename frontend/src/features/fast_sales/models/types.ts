// src/features/sales/types.ts

/**
 * Representa una venta en el frontend.
 *
 * Este modelo se utiliza para:
 * - Mostrar información en tablas y formularios
 * - Enviar datos a la API al crear o actualizar ventas
 *
 * Es un modelo plano, alineado con la estructura del backend.
 */
export interface Sale {
  /** Identificador único de la venta */
  id: number

  /** Nombre del producto vendido */
  product: string

  /** Cantidad de la venta */
  quantity: number

  /** Precio de la venta */
  price: number

  /** Nombre del vendedor */
  user: string

  /** Descripción adicional de la venta */
  description?: string
}

/**
 * Filtros disponibles para la consulta de ventas.
 *
 * Se utilizan al solicitar la lista de ventas
 * desde la API.
 */
export interface SalesQuery {
  /** Texto de búsqueda (producto, vendedor, descripción, etc.) */
  search?: string
}

/**
 * Representa la estructura de la venta
 * tal como la envía la API.
 *
 * Este tipo refleja fielmente el contrato del backend (Pydantic)
 * y debe usarse únicamente en servicios y mappers.
 */
export interface SaleApiResponse {
  id: number

  product: {
    id: number
    name: string
    type: string
    description?: string
    active: boolean
  }

  quantity: number
  price: number

  user: {
    id: number
    person: {
      id: number
      full_name: string
    }
    username: string
    email: string
  }

  description: string | null
}