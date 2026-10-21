// ─── Catálogos ────────────────────────────────────────────────────────────────

export interface ExpenseCategory {
  id: number
  name: string
}

export interface PaymentMethod {
  id: number
  name: string
}

/** Proceso de maquila al que quedó asociado un gasto */
export interface ExpenseProcess {
  id: number
  invoice_number: string
}

// ─── API shapes ───────────────────────────────────────────────────────────────

export interface GeneralExpenseApi {
  id: number
  expense_date: string
  amount: string
  category_id: number
  category?: ExpenseCategory
  payment_method_id?: number | null
  payment_method?: PaymentMethod | null
  process_id?: number | null
  process?: ExpenseProcess | null
  description: string
  created_by?: number | null
}

// ─── Mapped type ──────────────────────────────────────────────────────────────

export interface GeneralExpense {
  id: number
  expense_date: string
  amount: number
  category_id: number
  category_name: string
  payment_method_id?: number
  payment_method_name: string
  /** Solo los gastos creados desde el detalle de un proceso */
  process_id?: number
  process_invoice?: string
  description: string
}

// ─── Query / payloads ─────────────────────────────────────────────────────────

export interface ExpenseQuery {
  search?: string
  category_id?: number
  payment_method_id?: number
  date_from?: string
  date_to?: string
}

export interface CreateExpensePayload {
  expense_date: string
  amount: number
  category_id: number
  payment_method_id?: number
  description: string
}

export interface UpdateExpensePayload extends CreateExpensePayload {
  clear_payment_method?: boolean
}
