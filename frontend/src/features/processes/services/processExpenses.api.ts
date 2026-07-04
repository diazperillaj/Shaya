// features/processes/services/processExpenses.api.ts

import type { ProcessExpense, ProcessExpensePayload } from '../models/types'

const BASE_URL = '/api/v1/process-expenses'

/** Convierte la respuesta del backend (Decimals como string) al modelo del front */
const mapExpenseFromApi = (data: any): ProcessExpense => ({
  id: data.id,
  process_id: data.process_id,
  category: data.category,
  amount: Number(data.amount),
  expense_date: data.expense_date,
  observations: data.observations ?? undefined,
})

export const fetchProcessExpenses = async (
  processId: number,
): Promise<ProcessExpense[]> => {
  const res = await fetch(`${BASE_URL}/get?process_id=${processId}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error obteniendo los gastos del proceso')

  const data = await res.json()
  return data.map(mapExpenseFromApi)
}

export const createProcessExpense = async (
  processId: number,
  payload: ProcessExpensePayload,
): Promise<ProcessExpense> => {
  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ process_id: processId, ...payload }),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creando el gasto')

  return mapExpenseFromApi(data)
}

export const updateProcessExpense = async (
  expenseId: number,
  payload: ProcessExpensePayload,
): Promise<ProcessExpense> => {
  const res = await fetch(`${BASE_URL}/update/${expenseId}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error actualizando el gasto')

  return mapExpenseFromApi(data)
}

export const deleteProcessExpense = async (expenseId: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${expenseId}`, {
    method: 'DELETE',
    credentials: 'include',
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Error eliminando el gasto')
  }
}
