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

  /** Identificador único del inventario */
  id: i.id,

  /** Información del lote de pergamino */
  parchment_info: i.parchment_info,

  /** Tipo de producto (ej: Ground Coffee, Coffee Beans) */
  type: i.type,

  /** Cantidad del producto */
  amount: i.amount,

  /** Variedad del café */
  variety: i.variety,

  /** Nivel de tostión */
  roast_level: i.roast_level,

  /** Precio por unidad */
  unity_price: i.unity_price,

  /** Precio total */
  total_price: i.total_price,
})