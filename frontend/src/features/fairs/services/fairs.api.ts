import type {
  Fair,
  FairApi,
  FairReport,
  FairReportApi,
  CreateFairPayload,
  CreateFairInventoryPayload,
  UpdateFairInventoryPayload,
  CreateFairSalePayload,
  CreateFairExpensePayload,
  FairProduct,
  FairProductApi,
  FairProductPayload,
} from '../models/types'
import { mapFairFromApi, mapFairProductFromApi, mapFairReportFromApi } from '../mapper/fair.mapper'
import type { RoastedCoffeeProduct } from '../../sales/models/types'
import type { RoastedCoffeeApiResponse as MaquiladoApiResponse } from '../../roasted_coffee/models/types'

const BASE = '/api/v1/fairs'
const MAQUILADO_URL = '/api/v1/maquilado'

const opts = (method = 'GET', body?: unknown) => ({
  method,
  credentials: 'include' as const,
  headers: { 'Content-Type': 'application/json' },
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
})

async function handle<T>(res: Response): Promise<T> {
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail ?? 'Error en la solicitud')
  return data as T
}

// ─── Fairs CRUD ───────────────────────────────────────────────────────────────

export const fetchFairs = async (search?: string): Promise<Fair[]> => {
  const q = search ? `?search=${encodeURIComponent(search)}` : ''
  const res = await fetch(`${BASE}/get${q}`, opts())
  const data = await handle<FairApi[]>(res)
  return data.map(mapFairFromApi)
}

export const fetchFairById = async (id: number): Promise<Fair> => {
  const res = await fetch(`${BASE}/get/${id}`, opts())
  const data = await handle<FairApi>(res)
  return mapFairFromApi(data)
}

export const createFair = async (payload: CreateFairPayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/create`, opts('POST', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const updateFair = async (id: number, payload: CreateFairPayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/update/${id}`, opts('PUT', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const deleteFair = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE}/delete/${id}`, opts('DELETE'))
  if (!res.ok) { const d = await res.json(); throw new Error(d.detail ?? 'Error eliminando') }
}

export const closeFair = async (id: number): Promise<Fair> => {
  const res = await fetch(`${BASE}/${id}/close`, opts('POST'))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const fetchFairReport = async (id: number): Promise<FairReport> => {
  const res = await fetch(`${BASE}/${id}/report`, opts())
  return mapFairReportFromApi(await handle<FairReportApi>(res))
}

// ─── Inventory ────────────────────────────────────────────────────────────────

export const createFairInventory = async (fairId: number, payload: CreateFairInventoryPayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/inventory/create`, opts('POST', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const updateFairInventory = async (fairId: number, invId: number, payload: UpdateFairInventoryPayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/inventory/${invId}`, opts('PUT', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const deleteFairInventory = async (fairId: number, invId: number): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/inventory/${invId}`, opts('DELETE'))
  return mapFairFromApi(await handle<FairApi>(res))
}

// ─── Sales ────────────────────────────────────────────────────────────────────

export const createFairSale = async (fairId: number, payload: CreateFairSalePayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/sales/create`, opts('POST', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const updateFairSale = async (fairId: number, saleId: number, payload: CreateFairSalePayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/sales/${saleId}`, opts('PUT', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const deleteFairSale = async (fairId: number, saleId: number): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/sales/${saleId}`, opts('DELETE'))
  return mapFairFromApi(await handle<FairApi>(res))
}

// ─── Expenses ─────────────────────────────────────────────────────────────────

export const createFairExpense = async (fairId: number, payload: CreateFairExpensePayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/expenses/create`, opts('POST', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const updateFairExpense = async (fairId: number, expId: number, payload: CreateFairExpensePayload): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/expenses/${expId}`, opts('PUT', payload))
  return mapFairFromApi(await handle<FairApi>(res))
}

export const deleteFairExpense = async (fairId: number, expId: number): Promise<Fair> => {
  const res = await fetch(`${BASE}/${fairId}/expenses/${expId}`, opts('DELETE'))
  return mapFairFromApi(await handle<FairApi>(res))
}

// ─── Fair products catalog ────────────────────────────────────────────────────

const PRODUCTS_URL = '/api/v1/fair-products'

export const fetchFairProducts = async (): Promise<FairProduct[]> => {
  const res = await fetch(`${PRODUCTS_URL}/get`, opts())
  const data = await handle<FairProductApi[]>(res)
  return data.map(mapFairProductFromApi)
}

export const createFairProduct = async (payload: FairProductPayload): Promise<FairProduct> => {
  const res = await fetch(`${PRODUCTS_URL}/create`, opts('POST', payload))
  return mapFairProductFromApi(await handle<FairProductApi>(res))
}

export const updateFairProduct = async (id: number, payload: FairProductPayload): Promise<FairProduct> => {
  const res = await fetch(`${PRODUCTS_URL}/update/${id}`, opts('PUT', payload))
  return mapFairProductFromApi(await handle<FairProductApi>(res))
}

export const deleteFairProduct = async (id: number): Promise<void> => {
  const res = await fetch(`${PRODUCTS_URL}/delete/${id}`, opts('DELETE'))
  if (!res.ok) { const d = await res.json(); throw new Error(d.detail ?? 'Error eliminando') }
}

// ─── Support data ─────────────────────────────────────────────────────────────

export const fetchRoastedCoffeeForFair = async (): Promise<RoastedCoffeeProduct[]> => {
  const res = await fetch(MAQUILADO_URL + '/get', opts())
  const data: MaquiladoApiResponse[] = await handle(res)
  const products: RoastedCoffeeProduct[] = []
  for (const m of data) {
    for (const p of m.products) {
      products.push({
        detail_id: p.detail_id,
        roasted_coffee_id: m.id,
        product_id: p.product_id,
        name: p.name,
        grams_per_bag: p.quantity,
        quantity: p.quantity,
        remaining_quantity: p.remaining_quantity,
        variety: m.variety ?? undefined,
        process_id: m.process_id,
      })
    }
  }
  return products.filter((p) => p.remaining_quantity > 0)
}
