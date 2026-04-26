import type { ProductApiResponse } from '../models/types'

/**
 * Mapea un producto proveniente de la API
 * al modelo utilizado en el frontend.
 *
 * @param p Producto recibido desde la API
 * @returns Producto adaptado al modelo del frontend
 */
export const mapProductFromApi = (p: ProductApiResponse) => ({
  /** Identificador único del producto */
  id: p.id,

  /** Nombre del producto */
  name: p.name,

  /** Cantidad del producto */
  quantity: p.quantity,

  /** Tipo de producto (parchment, processed, other) */
  type: p.type,

  /**
   * Descripción del producto.
   * Se asigna un valor por defecto si la API no lo envía o es nulo.
   */
  description: p.description ?? 'Sin descripción',
})