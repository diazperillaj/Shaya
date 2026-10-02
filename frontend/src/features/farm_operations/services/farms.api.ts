import type { Farm, FarmPayload } from '../models/types'
import { request, toNumber } from './http'

type FarmApi = Omit<Farm, 'altitude' | 'total_area' | 'latitude' | 'longitude'> & {
  altitude: string | null
  total_area: string | null
  latitude: string | null
  longitude: string | null
}

const mapFarm = (farm: FarmApi): Farm => ({
  ...farm,
  altitude: toNumber(farm.altitude),
  total_area: toNumber(farm.total_area),
  latitude: toNumber(farm.latitude),
  longitude: toNumber(farm.longitude),
})

export const fetchFarms = async (search?: string): Promise<Farm[]> => {
  const farms = await request<FarmApi[]>('/farms/get', 'Error obteniendo las fincas', {
    query: { search },
  })
  return farms.map(mapFarm)
}

export const fetchFarm = async (id: number): Promise<Farm> =>
  mapFarm(await request<FarmApi>(`/farms/get/${id}`, 'Error obteniendo la finca'))

export const createFarm = async (payload: FarmPayload): Promise<Farm> =>
  mapFarm(await request<FarmApi>('/farms/create', 'Error creando la finca', {
    method: 'POST',
    body: payload,
  }))

export const updateFarm = async (id: number, payload: FarmPayload): Promise<Farm> =>
  mapFarm(await request<FarmApi>(`/farms/update/${id}`, 'Error actualizando la finca', {
    method: 'PUT',
    body: payload,
  }))

export const deleteFarm = async (id: number): Promise<void> => {
  await request(`/farms/delete/${id}`, 'Error eliminando la finca', { method: 'DELETE' })
}
