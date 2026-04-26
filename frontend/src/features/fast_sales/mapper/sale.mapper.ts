import type { SaleApiResponse } from '../models/types'

/**
 * Mapea una venta proveniente de la API
 * al modelo utilizado en el frontend.
 *
 * @param s Venta recibida desde la API
 * @returns Venta adaptada al modelo del frontend
 */
export const mapSaleFromApi = (s: SaleApiResponse) => ({
  /** Identificador único de la venta */
  id: s.id,

  /** Nombre del producto */
  product: s.product.name,

  /** Cantidad */
  quantity: s.quantity,

  /** Precio */
  price: s.price,

  /** Quien vende */
  user: s.user.person.full_name,

  /**
   * Descripción de la venta.
   * Se asigna un valor por defecto si la API no lo envía o es nulo.
   */
  description: s.description ?? 'Sin descripción',
})