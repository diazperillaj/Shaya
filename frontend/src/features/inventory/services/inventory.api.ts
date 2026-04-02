import type { Inventory, InventorysQuery } from '../models/types'
import { mapInventoryFromApi } from '../mapper/inventory.mapper'


const BASE_URL = 'http://localhost:8000/api/v1/inventory'

const FARMER_URL = 'http://localhost:8000/api/v1/farmers'

/* =======================
   GET
======================= */
export const fetchInventorys = async (filters?: InventorysQuery): Promise<Inventory[]> => {
  const query = new URLSearchParams()

  if (filters?.search) query.append('search', filters?.search)

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`,
    {
      credentials: 'include',
    })
  if (!res.ok) throw new Error('Error obteniendo inventario')

  const data = await res.json()

  console.log(data)

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
  const res = await fetch(`${FARMER_URL}/get`, {
    credentials: 'include',
  })

  const data = await res.json()

  return data.map((f: any) => ({
    label: `ID: ${f.person.id} - ${f.person.full_name}`,
    value: f.person.id,
  }))
}


/* =======================
   CREATE
======================= */
export const createInventory = async (Inventory: Inventory): Promise<Inventory> => {
  const payload = {
    farmer: Inventory.farmer,
    variety: Inventory.variety,
    elevation: Inventory.elevation,
    humidity: Inventory.humidity,
    yield_factor: Inventory.yield_factor,
    full_price: Inventory.full_price,
    price: Inventory.price,
    quantity: Inventory.quantity,
    stock: Inventory.stock,
    date: Inventory.date,
    observation: Inventory.observation,
  }

  console.log(payload)

  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  
  console.log(data.detail)

  if (!res.ok) {
    throw new Error(data.detail || 'Error creando inventario')
  }

  if (!res.ok) throw new Error('Error creando inventario')

  return mapInventoryFromApi(data)
}

/* =======================
   UPDATE
======================= */
export const updateInventory = async (Inventory: Inventory): Promise<Inventory> => {
    const payload = {
    farmer: Inventory.farmer,
    variety: Inventory.variety,
    elevation: Inventory.elevation,
    humidity: Inventory.humidity,
    yield_factor: Inventory.yield_factor,
    price: Inventory.price,
    full_price: Inventory.full_price,
    quantity: Inventory.quantity,
    stock: Inventory.stock,
    date: Inventory.date,
    observation: Inventory.observation,
  }

  const res = await fetch(`${BASE_URL}/update/${Inventory.id}`, {
    method: 'PUT',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  console.log(data.detail)

  if (!res.ok) {
    throw new Error(data.detail || 'Error actualizando inventario')
  }

  if (!res.ok) throw new Error('Error actualizando inventario')

  return mapInventoryFromApi(data)
}

/* =======================
   DELETE
======================= */

export const deleteInventory = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: "include",
  })

  if (!res.ok) throw new Error('Error eliminando cliente')
}



