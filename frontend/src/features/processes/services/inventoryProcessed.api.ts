// features/inventoryProcessed/services/inventoryProcessed.api.ts

import type {
  Process,
  ProcessDetail,
  ProcessQuery,
  CreateProcessPayload,
  ProcessWithDetails,
  ProcessCosts,
} from '../models/types'
import { mapDetalleFromApi, mapProcesoFromApi } from '../mapper/inventoryProcessed.mapper'
import type { Parchment  } from '../mapper/parchment.mapper'
import { mapParchmentFromApi } from '../mapper/parchment.mapper'
import type { Product } from '../../products/models/types'
import { mapProductFromApi } from '../../products/mapper/product.mapper'

const BASE_URL = '/api/v1/process'
const PARCHMENT_URL = '/api/v1/inventory'
const PRODUCT_URL = '/api/v1/products'

// import type { Inventory } from '../../inventory/models/types';
  

export const fetchParchments = async (): Promise<Parchment[]> => {
  const res = await fetch(`${PARCHMENT_URL}/get`, {
    credentials: 'include',
  })

  if (!res.ok) {
    throw new Error('Error fetching parchments')
  }

  const data = await res.json()

  return data.map(mapParchmentFromApi)
}


export const fetchProducts = async (): Promise<Product[]> => {
  const res = await fetch(`${PRODUCT_URL}/get`, {
    credentials: 'include',
  })

  if (!res.ok) {
    throw new Error('Error fetching products')
  }

  const data = await res.json()

  return data.map(mapProductFromApi)
}



// ─── GET all processes ────────────────────────────────────────────────────────

export const fetchProcesos = async (filters?: ProcessQuery): Promise<Process[]> => {
  const query = new URLSearchParams()
  if (filters?.search) query.append('search', filters.search)

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error fetching processes')

  const data = await res.json()

  console.log(data);

  return data.map(mapProcesoFromApi)
}

// ─── GET details of a single process ─────────────────────────────────────────

export const fetchDetallesByProceso = async (
  procesoId: number,
): Promise<ProcessDetail[]> => {
  const res = await fetch(`${BASE_URL}/get/${procesoId}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error fetching process details')

  const data = await res.json()
  return (data.details || []).map(mapDetalleFromApi)
}

export const fetchProcesoById = async (
  procesoId: number,
): Promise<ProcessWithDetails> => {
  const res = await fetch(`${BASE_URL}/get/${procesoId}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error fetching process')

  const data = await res.json()
  return {
    process: mapProcesoFromApi(data),
    details: (data.details || []).map(mapDetalleFromApi),
  }
}

// ─── CREATE process + details in one request ──────────────────────────────────
/*
  Expected backend endpoint:  POST /api/v1/processes/create
  Expected payload shape:
  {
    invoice_number:  string,
    process_date:    string,        // "YYYY-MM-DD"
    farmer_name:     string,
    parchment_kg:    number,
    observations?:   string,
    details: [
      {
        product_name:  string,
        bag_quantity:  number,
        grams_per_bag: number,
        unit_value:    number,
        observations?: string,
      }
    ]
  }

  The backend should:
  - Compute resultant_kg = sum(bag_quantity * grams_per_bag / 1000)
  - Compute yield_percentage = (resultant_kg / parchment_kg) * 100
  - Compute subtotal = sum(unit_value * bag_quantity) per detail
  - Compute IVA = subtotal * 0.052
  - Compute total = subtotal + IVA
  - Persist Proceso + DetallesProceso and return the created Proceso
*/
export const createProceso = async (
  payload: CreateProcessPayload,
): Promise<Process> => {
  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  
  console.log(payload);
  
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creating process')

  return mapProcesoFromApi(data)
}

// ─── UPDATE process (header only; details managed separately) ────────────────
/*
  Expected backend endpoint:  PUT /api/v1/processes/update/:id
  Payload: same shape as create but without `details`.
  Returns the updated Proceso.
*/
export const updateProceso = async (
  id: number,
  payload: CreateProcessPayload,
): Promise<Process> => {
  const res = await fetch(`${BASE_URL}/update/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error updating process')

  return mapProcesoFromApi(data)
}

// ─── DELETE process ───────────────────────────────────────────────────────────

export const deleteProceso = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Error eliminando el proceso')
  }
}

// ─── GET cost breakdown of a process ──────────────────────────────────────────

export const fetchProcessCosts = async (
  procesoId: number,
): Promise<ProcessCosts> => {
  const res = await fetch(`${BASE_URL}/${procesoId}/costs`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error obteniendo los costos del proceso')

  const data = await res.json()

  return {
    process_id: data.process_id,
    parchment_cost: Number(data.parchment?.cost ?? 0),
    parchment_kg: Number(data.parchment?.parchment_kg ?? 0),
    maquila_total: Number(data.maquila?.total ?? 0),
    process_expenses: (data.process_expenses || []).map((e: any) => ({
      id: e.id,
      process_id: data.process_id,
      category: e.category,
      amount: Number(e.amount),
      expense_date: e.expense_date,
      observations: e.observations ?? undefined,
    })),
    process_expenses_total: Number(data.process_expenses_total ?? 0),
    total_grams: Number(data.total_grams ?? 0),
    total_cost: Number(data.total_cost ?? 0),
    products: (data.products || []).map((p: any) => ({
      product_id: p.product_id,
      product_name: p.product_name ?? undefined,
      bag_quantity: p.bag_quantity,
      grams_per_bag: p.grams_per_bag,
      maquila_line_total: Number(p.maquila_line_total ?? 0),
      product_expenses_per_bag: Number(p.product_expenses_per_bag ?? 0),
      unit_cost: p.unit_cost == null ? null : Number(p.unit_cost),
      total_cost: p.total_cost == null ? null : Number(p.total_cost),
    })),
  }
}