// features/inventoryProcessed/models/types.ts

// ─── Process ─────────────────────────────────────────────────────────────────

/**
 * Represents a roasting/processing batch in the frontend.
 * A process consumes parchment coffee and yields roasted bags.
 */
export interface Process {
  id: number

  /** Invoice / bill number from the roaster */
  invoice_number: string

  /** Date the process took place */
  process_date: string

  /** Farmer linked to the parchment used */
  parchment_id: number

  /** Parchment coffee sent (Kg) — entered manually */
  parchment_kg: number

  /** Resulting roasted weight (Kg) — sum of detail lines */
  resultant_kg: number

  /** Rendimiento = (Resultante / Pergamino_Kg) * 100 */
  yield_percentage: number

  /** Sum of (Valor_Unitario * Cantidad_Bolsas) for all detail lines */
  subtotal: number

  /** Subtotal * 0.052 */
  iva: number

  /** Subtotal + IVA */
  total: number

  /** Optional notes */
  observations?: string
}

// ─── Process Detail ──────────────────────────────────────────────────────────

/**
 * A single line inside a process (one product/presentation).
 */
export interface ProcessDetail {
  id: number

  /** FK to Proceso */
  p_id: number

  /** Date (usually same as the parent process) */
  process_date: string

  /** Product name (e.g. "Tostado 250g", "Tostado 1Kg") */
  product_id: number

  /** Number of bags produced */
  bag_quantity: number

  /** Weight per bag in grams */
  grams_per_bag: number

  /** Price per bag */
  unit_value: number

  /** unit_value * bag_quantity * 0.052 */
  iva: number

  /** (unit_value * bag_quantity) + IVA */
  total: number

  /** Optional notes */
  observations?: string
}

// ─── Query filters ────────────────────────────────────────────────────────────

export interface ProcessQuery {
  search?: string
}

// ─── API response shapes ──────────────────────────────────────────────────────

export interface ProcessApiResponse {
  id: number
  invoice_number: string
  process_date: string
  parchment_id: number
  parchment_kg: string
  resultant_kg: string
  yield_percentage: string
  subtotal: string
  iva: string
  total: string
  observations?: string
}

export interface ProcessDetailApiResponse {
  id: number
  process_id: number
  date: string
  product_id: number
  bag_quantity: number
  grams_per_bag: number
  unit_value: string
  iva: string
  total: string
  observations?: string
}

// ─── Create payloads (what we send to the backend) ───────────────────────────

export interface CreateProcessDetailPayload {
  product_id: number | null
  bag_quantity: number
  grams_per_bag: number
  unit_value: number
  observations?: string
}

export interface CreateProcessPayload {
  invoice_number: string
  process_date: string
  parchment_id: number
  parchment_kg: number
  observations?: string
  details: CreateProcessDetailPayload[]
}