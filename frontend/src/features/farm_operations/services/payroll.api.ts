import type {
  DayLabor,
  DayLaborPayload,
  PaymentItem,
  PaymentResult,
  PaymentSelection,
} from '../models/types'
import { request, toNumber } from './http'

/* Jornales y pagos a los trabajadores */

type DayLaborApi = Omit<DayLabor, 'daily_value'> & { daily_value: string }
type PaymentItemApi = Omit<PaymentItem, 'amount' | 'kg_collected'> & { amount: string; kg_collected: string | null }

const mapLabor = (labor: DayLaborApi): DayLabor => ({ ...labor, daily_value: toNumber(labor.daily_value) ?? 0 })

const mapItem = (item: PaymentItemApi): PaymentItem => ({
  ...item,
  amount: toNumber(item.amount) ?? 0,
  kg_collected: toNumber(item.kg_collected),
})

export const fetchDayLabors = async (farmId: number): Promise<DayLabor[]> => {
  const labors = await request<DayLaborApi[]>('/day-labors/get', 'Error obteniendo los jornales', {
    query: { farm_id: farmId },
  })
  return labors.map(mapLabor)
}

export const createDayLabor = async (payload: DayLaborPayload): Promise<DayLabor> =>
  mapLabor(await request<DayLaborApi>('/day-labors/create', 'Error registrando el jornal', {
    method: 'POST',
    body: payload,
  }))

export const updateDayLabor = async (id: number, payload: DayLaborPayload): Promise<DayLabor> =>
  mapLabor(await request<DayLaborApi>(`/day-labors/update/${id}`, 'Error actualizando el jornal', {
    method: 'PUT',
    body: payload,
  }))

export const deleteDayLabor = async (id: number): Promise<void> => {
  await request(`/day-labors/delete/${id}`, 'Error eliminando el jornal', { method: 'DELETE' })
}

/** Recolección y jornales de la finca, pagados o pendientes */
export const fetchPaymentItems = async (farmId: number, paid: boolean): Promise<PaymentItem[]> => {
  const items = await request<PaymentItemApi[]>('/payments/get', 'Error obteniendo los pagos', {
    query: { farm_id: farmId, paid },
  })
  return items.map(mapItem)
}

const toResult = (result: { count: number; total: string }): PaymentResult => ({
  count: result.count,
  total: toNumber(result.total) ?? 0,
})

export const payItems = async (selection: PaymentSelection, paidAt: string): Promise<PaymentResult> =>
  toResult(await request('/payments/pay', 'Error registrando el pago', {
    method: 'POST',
    body: { ...selection, paid_at: paidAt },
  }))

export const unpayItems = async (selection: PaymentSelection): Promise<PaymentResult> =>
  toResult(await request('/payments/unpay', 'Error deshaciendo el pago', { method: 'POST', body: selection }))
