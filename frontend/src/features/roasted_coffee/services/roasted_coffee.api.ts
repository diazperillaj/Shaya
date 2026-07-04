// src/features/roasted_coffee/services/roasted_coffee.api.ts
import type { RoastedCoffeeApiResponse, RoastedCoffeeQuery, RoastedCoffeeRow } from '../models/types'
import { mapRoastedCoffeeFromApi } from '../mapper/roasted_coffee.mapper'

const BASE_URL = '/api/v1/maquilado'

/* =======================
   GET all
======================= */
export const fetchRoastedCoffees = async (filters?: RoastedCoffeeQuery): Promise<RoastedCoffeeRow[]> => {
  const query = new URLSearchParams()
  if (filters?.search) query.append('search', filters.search)

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`, {
    credentials: 'include',
  })

  if (!res.ok) throw new Error('Error obteniendo maquilados')

  const data: RoastedCoffeeApiResponse[] = await res.json()
  const rows = data.flatMap(mapRoastedCoffeeFromApi)

  if (!filters?.search) return rows

  // El backend filtra a nivel de maquilado; aquí filtramos las filas planas
  // para que el producto también quede exactamente acotado.
  const s = filters.search.toLowerCase()
  return rows.filter(row =>
    String(row.maquilado_id).includes(s) ||
    String(row.process_id).includes(s) ||
    row.variety.toLowerCase().includes(s) ||
    row.product_name.toLowerCase().includes(s)
  )
}

/* =======================
   DELETE
======================= */
export const deleteRoastedCoffee = async (maquiladoId: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${maquiladoId}`, {
    method: 'DELETE',
    credentials: 'include',
  })

  if (!res.ok) throw new Error('Error eliminando maquilado')
}
