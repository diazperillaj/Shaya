// src/features/roasted_coffee/models/types.ts

/** Fila plana para la tabla (un registro por producto del maquilado) */
export interface RoastedCoffeeRow {
  maquilado_id: number
  detail_id: number
  process_id: number
  variety: string
  product_name: string
  quantity: number
  remaining_quantity: number
  observations: string | null
}

/** Filtros para la consulta */
export interface RoastedCoffeeQuery {
  search?: string
}

/** Estructura del producto tal como la envía la API */
export interface RoastedCoffeeProductApiResponse {
  detail_id: number
  product_id: number
  name: string
  quantity: number
  remaining_quantity: number
}

/** Estructura del maquilado tal como la envía la API */
export interface RoastedCoffeeApiResponse {
  id: number
  process_id: number
  variety: string | null
  observations: string | null
  products: RoastedCoffeeProductApiResponse[]
}
