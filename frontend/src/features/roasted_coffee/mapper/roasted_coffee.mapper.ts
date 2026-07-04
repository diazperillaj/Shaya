// src/features/roasted_coffee/mapper/roasted_coffee.mapper.ts
import type { RoastedCoffeeApiResponse, RoastedCoffeeRow } from '../models/types'

/**
 * Expande un maquilado de la API en filas planas (una por producto).
 * La DataTable muestra ID maquila, variedad, producto y cantidad restante
 * directamente sin modal de detalle adicional.
 */
export const mapRoastedCoffeeFromApi = (m: RoastedCoffeeApiResponse): RoastedCoffeeRow[] =>
  m.products.map(p => ({
    maquilado_id: m.id,
    detail_id: p.detail_id,
    process_id: m.process_id,
    variety: m.variety ?? '—',
    product_name: p.name,
    quantity: p.quantity,
    remaining_quantity: p.remaining_quantity,
    observations: m.observations,
  }))
