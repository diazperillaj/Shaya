import type { InventoryApiResponse } from '../models/types'

/**
 * Mapea un registro de inventario proveniente de la API
 * al modelo utilizado en el frontend.
 *
 * Este mapper desacopla el contrato del backend
 * del modelo plano consumido por la interfaz.
 *
 * @param i Inventario recibido desde la API
 * @returns Inventario adaptado al modelo del frontend
 */
export const mapInventoryFromApi = (i: InventoryApiResponse) => ({

  /** Identificador único del lote */
  id: i.id,

  /** Producto */
  product: i.product,

  /** Caficultor */
  farmer: i.farmer,

  /** Variedad */
  variety: i.variety,

  /** Altitud del lote */
  elevation: i.elevation,

  /** Humedad del lote */
  humidity: i.humidity,

  /** Factor de rendimiento del lote */
  yield_factor: i.yield_factor,

  /** Precio de compra */
  price: i.price,

  /** Precio por carga */
  full_price: i.full_price,

  /** Cantidad inicial */
  quantity: i.quantity,

  /** Stock actual */
  stock: i.stock,

  /** Fecha de compra */
  date: i.date,

  /**
   * Observaciones.
   * Se normaliza a string si la API envía null.
   */
  observation: i.observation ?? 'Sin observación',
})