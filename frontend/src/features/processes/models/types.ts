


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
  farmer_name?: string
  parchment_variety?: string

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
  product_name?: string

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
  parchment?: {
    id: number
    variety?: string
    farmer?: {
      person?: {
        full_name?: string
      }
    }
  }
}

export interface ProcessDetailApiResponse {
  id: number
  process_id: number
  date: string
  product_id: number
  product?: {
    id: number
    name: string
  }
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

export interface ProcessWithDetails {
  process: Process
  details: ProcessDetail[]
}

// ─── Process expenses (gastos de producción del proceso) ─────────────────────

/**
 * Gasto adicional de un proceso (transporte, mano de obra, etc.).
 * El valor es TOTAL del proceso y se prorratea por gramos.
 */
export interface ProcessExpense {
  id: number
  process_id: number
  category: string
  amount: number
  expense_date: string
  observations?: string
}

/** Payload de creación/edición de un gasto de proceso */
export interface ProcessExpensePayload {
  category: string
  amount: number
  expense_date: string
  observations?: string
}

// ─── Process costs (desglose de GET /process/{id}/costs) ─────────────────────

/** Costos calculados de un producto dentro del proceso */
export interface ProcessCostProduct {
  product_id: number
  product_name?: string
  bag_quantity: number
  grams_per_bag: number
  maquila_line_total: number
  product_expenses_per_bag: number
  /** Costo por bolsa congelado; null = no calculable (ej. inventario inicial) */
  unit_cost: number | null
  total_cost: number | null
}

/** Desglose completo de costos de un proceso */
export interface ProcessCosts {
  process_id: number
  parchment_cost: number
  parchment_kg: number
  maquila_total: number
  process_expenses: ProcessExpense[]
  process_expenses_total: number
  total_grams: number
  total_cost: number
  products: ProcessCostProduct[]
}