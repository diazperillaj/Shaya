export type MovementDirection = 'entry' | 'exit'

export interface RoastedMovementDetail {
  id: number
  detail_roasted_coffee_id: number
  roasted_coffee_id: number
  product_name: string
  quantity: number
  direction: MovementDirection
  /** True si esta línea creó el lote (entrada de producto nuevo) */
  created_lot: boolean
}

export interface RoastedMovement {
  id: number
  movement_date: string
  observations: string | null
  created_by: number | null
  details: RoastedMovementDetail[]
}

/**
 * Línea de un movimiento:
 * - Salida: detail_roasted_coffee_id (lote existente).
 * - Entrada a lote existente: detail_roasted_coffee_id.
 * - Entrada de producto nuevo: product_id (+ roasted_coffee_id si no es
 *   reempaque; en reempaque hereda el maquilado del lote de origen).
 * - grams_per_bag: obligatorio en entradas de reempaque.
 * - manual_unit_cost: opcional, solo entradas puras de producto nuevo.
 */
export interface RoastedMovementDetailCreate {
  detail_roasted_coffee_id?: number
  product_id?: number
  roasted_coffee_id?: number
  quantity: number
  grams_per_bag?: number
  manual_unit_cost?: number
  direction: MovementDirection
}

export interface RoastedMovementCreate {
  movement_date: string
  observations?: string
  details: RoastedMovementDetailCreate[]
}
