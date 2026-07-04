// features/products/services/productExpenses.api.ts

import type { ProductExpense, ProductExpensePayload } from '../models/types'

const BASE_URL = '/api/v1/product-expenses'

/** Convierte la respuesta del backend (Decimals como string) al modelo del front */
const mapExpenseFromApi = (data: any): ProductExpense => ({
  id: data.id,
  product_id: data.product_id,
  category: data.category,
  amount: Number(data.amount),
  observations: data.observations ?? undefined,
})

export const fetchProductExpenses = async (
  productId: number,
): Promise<ProductExpense[]> => {
  const res = await fetch(`${BASE_URL}/get?product_id=${productId}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error obteniendo los costos de producción')

  const data = await res.json()
  return data.map(mapExpenseFromApi)
}

export const createProductExpense = async (
  productId: number,
  payload: ProductExpensePayload,
): Promise<ProductExpense> => {
  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id: productId, ...payload }),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creando el costo')

  return mapExpenseFromApi(data)
}

export const updateProductExpense = async (
  expenseId: number,
  payload: ProductExpensePayload,
): Promise<ProductExpense> => {
  const res = await fetch(`${BASE_URL}/update/${expenseId}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error actualizando el costo')

  return mapExpenseFromApi(data)
}

export const deleteProductExpense = async (expenseId: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${expenseId}`, {
    method: 'DELETE',
    credentials: 'include',
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Error eliminando el costo')
  }
}
