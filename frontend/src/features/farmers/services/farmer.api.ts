import type { Farmer, FarmersQuery } from '../models/types'
import { mapFarmerFromApi } from '../mapper/farmer.mapper'


const BASE_URL = 'http://localhost:8000/api/v1/farmers'

/* =======================
   GET
======================= */
export const fetchFarmers = async (filters?: FarmersQuery): Promise<Farmer[]> => {
  const query = new URLSearchParams()

  if (filters?.search) query.append('search', filters?.search)

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`,
    {
      credentials: 'include',
    })
  if (!res.ok) throw new Error('Error obteniendo caficultors')

  const data = await res.json()

  console.log(data)

  return data.map(mapFarmerFromApi)
}

/* =======================
   CREATE
======================= */
export const createFarmer = async (Farmer: Farmer): Promise<Farmer> => {
  const payload = {
    farm_name: Farmer.farm_name,
    farm_location: Farmer.farm_location,
    person: {
      full_name: Farmer.name,
      document: Farmer.document,
      email: Farmer.email,
      phone: Farmer.phone,
      observation: Farmer.observation,
    },
  }

  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()


  if (!res.ok) {
    throw new Error(data.detail || 'Error creando caficultor')
  }

  if (!res.ok) throw new Error('Error creando caficultor')

  return mapFarmerFromApi(data)
}

/* =======================
   UPDATE
======================= */
export const updateFarmer = async (Farmer: Farmer): Promise<Farmer> => {
  const payload: any = {
    farm_name: Farmer.farm_name,
    farm_location: Farmer.farm_location,
    person: {
      full_name: Farmer.name,
      document: Farmer.document,
      email: Farmer.email,
      phone: Farmer.phone,
      observation: Farmer.observation,
    },
  }

  const res = await fetch(`${BASE_URL}/update/${Farmer.id}`, {
    method: 'PUT',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  console.log(data.detail)

  if (!res.ok) {
    throw new Error(data.detail || 'Error creando caficultor')
  }

  if (!res.ok) throw new Error('Error creando caficultor')

  return mapFarmerFromApi(data)

  if (!res.ok) throw new Error('Error actualizando caficultor')

  return mapFarmerFromApi(await res.json())
}

/* =======================
   DELETE
======================= */

export const deleteFarmer = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: "include",
  })

  if (!res.ok) throw new Error('Error eliminando caficultor')
}



