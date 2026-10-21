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

/* =======================
   Tablero del inventario (GET /maquilado/dashboard)
======================= */

export interface InventoryLotProduct {
  detail_id: number
  product_id: number
  name: string
  /** Existencia inicial del proceso + entradas por movimientos */
  total_in: number
  /** Ventas + ferias + salidas por movimientos */
  total_out: number
  remaining_quantity: number
  unit_cost: number | null
}

export interface InventoryLot {
  id: number
  process_id: number
  invoice_number: string
  process_date: string
  variety: string | null
  farmer_name: string | null
  farm_name: string | null
  altitude: number | null
  yield_percentage: number | null
  observations: string | null
  products: InventoryLotProduct[]
}

export type InventoryEventKind = 'process' | 'sale' | 'fair' | 'movement' | 'adjustment'

/** Entrada (+) o salida (−) de unidades de un producto de un lote */
export interface InventoryEvent {
  event_date: string
  lot_id: number
  detail_id: number
  product_id: number
  product_name: string
  kind: InventoryEventKind
  quantity: number
  reference: string
  note: string | null
}

export interface InventoryDashboard {
  lots: InventoryLot[]
  /** Ordenados por fecha; por producto de lote suman su cantidad restante */
  events: InventoryEvent[]
}
