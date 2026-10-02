import type { ClimatePayload, ClimateRecord } from '../models/types'
import { request, toNumber } from './http'

type ClimateApi = Omit<ClimateRecord, 'rainfall_mm' | 'temp_min_c' | 'temp_max_c'> & {
  rainfall_mm: string | null
  temp_min_c: string | null
  temp_max_c: string | null
}

const mapRecord = (record: ClimateApi): ClimateRecord => ({
  ...record,
  rainfall_mm: toNumber(record.rainfall_mm),
  temp_min_c: toNumber(record.temp_min_c),
  temp_max_c: toNumber(record.temp_max_c),
})

export const fetchClimateRecords = async (farmId: number): Promise<ClimateRecord[]> => {
  const records = await request<ClimateApi[]>('/climate-records/get', 'Error obteniendo el clima', {
    query: { farm_id: farmId },
  })
  return records.map(mapRecord)
}

export const createClimateRecord = async (farmId: number, payload: ClimatePayload): Promise<ClimateRecord> =>
  mapRecord(await request<ClimateApi>('/climate-records/create', 'Error registrando el clima', {
    method: 'POST',
    body: { ...payload, farm_id: farmId },
  }))

export const updateClimateRecord = async (id: number, payload: ClimatePayload): Promise<ClimateRecord> =>
  mapRecord(await request<ClimateApi>(`/climate-records/update/${id}`, 'Error actualizando el registro', {
    method: 'PUT',
    body: payload,
  }))

export const deleteClimateRecord = async (id: number): Promise<void> => {
  await request(`/climate-records/delete/${id}`, 'Error eliminando el registro', { method: 'DELETE' })
}
