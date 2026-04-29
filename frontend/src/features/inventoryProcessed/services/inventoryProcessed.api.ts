// features/inventoryProcessed/services/inventoryProcessed.api.ts

import type {
  Process,
  ProcessDetail,
  ProcessQuery,
  CreateProcessPayload,
} from '../models/types'
import { mapDetalleFromApi, mapProcesoFromApi } from '../mapper/inventoryProcessed.mapper'
import type { Parchment  } from '../mapper/parchment.mapper'
import { mapParchmentFromApi } from '../mapper/parchment.mapper'
import type { Product } from '../../products/models/types'
import { mapProductFromApi } from '../../products/mapper/product.mapper'

const BASE_URL = 'http://localhost:8000/api/v1/processes'
const PARCHMENT_URL = 'http://localhost:8000/api/v1/inventory'
const PRODUCT_URL = 'http://localhost:8000/api/v1/products'

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
  return data.map(mapProcesoFromApi)
}

// ─── GET details of a single process ─────────────────────────────────────────

export const fetchDetallesByProceso = async (
  procesoId: number,
): Promise<ProcessDetail[]> => {
  const res = await fetch(`${BASE_URL}/${procesoId}/details`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error fetching process details')

  const data = await res.json()
  return data.map(mapDetalleFromApi)
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
  payload: Omit<CreateProcessPayload, 'details'>,
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
  if (!res.ok) throw new Error('Error deleting process')
}