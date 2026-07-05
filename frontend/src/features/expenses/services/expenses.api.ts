import type {
  CreateExpensePayload,
  ExpenseCategory,
  ExpenseQuery,
  GeneralExpense,
  GeneralExpenseApi,
  PaymentMethod,
  UpdateExpensePayload,
} from '../models/types'
import { mapExpenseFromApi } from '../mapper/expense.mapper'

const EXPENSES_URL = '/api/v1/general-expenses'
const CATEGORIES_URL = '/api/v1/expense-categories'
const METHODS_URL = '/api/v1/payment-methods'

// ─── Gastos generales ─────────────────────────────────────────────────────────

export const fetchExpenses = async (filters?: ExpenseQuery): Promise<GeneralExpense[]> => {
  const query = new URLSearchParams()
  if (filters?.search) query.append('search', filters.search)
  if (filters?.category_id) query.append('category_id', String(filters.category_id))
  if (filters?.payment_method_id) query.append('payment_method_id', String(filters.payment_method_id))
  if (filters?.date_from) query.append('date_from', filters.date_from)
  if (filters?.date_to) query.append('date_to', filters.date_to)

  const res = await fetch(`${EXPENSES_URL}/get?${query.toString()}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error obteniendo gastos')

  const data: GeneralExpenseApi[] = await res.json()
  return data.map(mapExpenseFromApi)
}

export const createExpense = async (payload: CreateExpensePayload): Promise<GeneralExpense> => {
  const res = await fetch(`${EXPENSES_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creando gasto')
  return mapExpenseFromApi(data)
}

export const updateExpense = async (
  id: number,
  payload: UpdateExpensePayload,
): Promise<GeneralExpense> => {
  const res = await fetch(`${EXPENSES_URL}/update/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error actualizando gasto')
  return mapExpenseFromApi(data)
}

export const deleteExpense = async (id: number): Promise<void> => {
  const res = await fetch(`${EXPENSES_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Error eliminando gasto')
  }
}

// ─── Categorías ───────────────────────────────────────────────────────────────

export const fetchExpenseCategories = async (): Promise<ExpenseCategory[]> => {
  const res = await fetch(`${CATEGORIES_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo categorías')
  return res.json()
}

export const createExpenseCategory = async (name: string): Promise<ExpenseCategory> => {
  const res = await fetch(`${CATEGORIES_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creando categoría')
  return data
}

export const updateExpenseCategory = async (id: number, name: string): Promise<ExpenseCategory> => {
  const res = await fetch(`${CATEGORIES_URL}/update/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error actualizando categoría')
  return data
}

export const deleteExpenseCategory = async (id: number): Promise<void> => {
  const res = await fetch(`${CATEGORIES_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Error eliminando categoría')
  }
}

// ─── Métodos de pago ──────────────────────────────────────────────────────────

export const fetchPaymentMethods = async (): Promise<PaymentMethod[]> => {
  const res = await fetch(`${METHODS_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo métodos de pago')
  return res.json()
}

export const createPaymentMethod = async (name: string): Promise<PaymentMethod> => {
  const res = await fetch(`${METHODS_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creando método de pago')
  return data
}

export const updatePaymentMethod = async (id: number, name: string): Promise<PaymentMethod> => {
  const res = await fetch(`${METHODS_URL}/update/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error actualizando método de pago')
  return data
}

export const deletePaymentMethod = async (id: number): Promise<void> => {
  const res = await fetch(`${METHODS_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Error eliminando método de pago')
  }
}
