import type { Inventory, InventorysQuery } from '../models/types'
import { mapInventoryFromApi } from '../mapper/inventory.mapper'

const BASE_URL = 'http://localhost:8000/api/v1/inventory'
const FARMER_URL = 'http://localhost:8000/api/v1/farmers'

/* =======================
   HELPER: extrae el farmer_id sin importar si llega
   como objeto { id: number } o directamente como number
   (el select del modal guarda solo el value = id)
======================= */
const extractFarmerId = (farmer: any): number => {
  if (typeof farmer === 'object' && farmer !== null) return farmer.id
  return Number(farmer)
}

/* =======================
   GET
======================= */
export const fetchInventorys = async (filters?: InventorysQuery): Promise<Inventory[]> => {
  const query = new URLSearchParams()
  if (filters?.search) query.append('search', filters.search)

  const res = await fetch(`${BASE_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo inventario')

  const data = await res.json()
  return data.map(mapInventoryFromApi)
}

/* =======================
   GET FARMERS TO SELECT
======================= */
export interface FarmerOption {
  label: string
  value: number
}

export const getFarmers = async (): Promise<FarmerOption[]> => {
  const res = await fetch(`${FARMER_URL}/get`, { credentials: 'include' })
  const data = await res.json()

  return data.map((f: any) => ({
    label: `ID: ${f.id} - ${f.person.full_name}`,
    value: f.id,
  }))
}

/* =======================
   CREATE
======================= */
export const createInventory = async (inventory: Inventory): Promise<Inventory> => {
  const payload = {
    farmer_id: extractFarmerId(inventory.farmer),  // ✅ requerido por el backend
    product_id: 1,                                  // ✅ siempre 1

    variety: inventory.variety,

    altitude: inventory.elevation,
    humidity: inventory.humidity,

    purchase_price: inventory.price,
    full_price: inventory.full_price,

    initial_quantity: inventory.quantity,

    purchase_date: inventory.date,

    observations: inventory.observation ?? '',
  }

  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  if (!res.ok) throw new Error(data.detail || 'Error creando inventario')

  return mapInventoryFromApi(data)
}

/* =======================
   UPDATE
======================= */
export const updateInventory = async (inventory: Inventory): Promise<Inventory> => {

  const payload = {
    farmer_id: extractFarmerId(inventory.farmer),
    product_id: 1,

    variety: inventory.variety,

    altitude: inventory.elevation,
    humidity: inventory.humidity,

    purchase_price: inventory.price,
    full_price: inventory.full_price,

    remaining_quantity: inventory.remaining_quantity,

    purchase_date: inventory.date,

    observations: inventory.observation ?? '',
  }

  const res = await fetch(`${BASE_URL}/update/${inventory.id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  if (!res.ok) throw new Error(data.detail || 'Error actualizando inventario')

  return mapInventoryFromApi(data)
}

/* =======================
   DELETE
======================= */
export const deleteInventory = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })

  if (!res.ok) throw new Error('Error eliminando inventario')
}