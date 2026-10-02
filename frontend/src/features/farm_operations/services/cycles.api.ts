import type { CropCycle, CycleDetail, CycleUpdatePayload, RecordSummary } from '../models/types'
import { request, toNumber } from './http'

type SummaryApi = Omit<RecordSummary, 'total_cost'> & { total_cost: string | null }
type CycleDetailApi = Omit<CycleDetail, 'summary'> & { summary: SummaryApi[] }

const mapDetail = (cycle: CycleDetailApi): CycleDetail => ({
  ...cycle,
  summary: cycle.summary.map((item) => ({ ...item, total_cost: toNumber(item.total_cost) })),
})

/** Ciclos de un lote, del más reciente al más antiguo */
export const fetchCycles = async (plotId: number): Promise<CropCycle[]> =>
  request<CropCycle[]>('/crop-cycles/get', 'Error obteniendo los ciclos', { query: { plot_id: plotId } })

export const fetchCycle = async (id: number): Promise<CycleDetail> =>
  mapDetail(await request<CycleDetailApi>(`/crop-cycles/get/${id}`, 'Error obteniendo el ciclo'))

export const createCycle = async (payload: {
  plot_id: number
  start_date: string
  observations: string | null
}): Promise<CycleDetail> =>
  mapDetail(await request<CycleDetailApi>('/crop-cycles/create', 'Error abriendo el ciclo', {
    method: 'POST',
    body: payload,
  }))

export const updateCycle = async (id: number, payload: CycleUpdatePayload): Promise<CycleDetail> =>
  mapDetail(await request<CycleDetailApi>(`/crop-cycles/update/${id}`, 'Error actualizando el ciclo', {
    method: 'PUT',
    body: payload,
  }))

export const closeCycle = async (id: number, endDate: string): Promise<CycleDetail> =>
  mapDetail(await request<CycleDetailApi>(`/crop-cycles/${id}/close`, 'Error cerrando el ciclo', {
    method: 'POST',
    body: { end_date: endDate },
  }))

export const reopenCycle = async (id: number): Promise<CycleDetail> =>
  mapDetail(await request<CycleDetailApi>(`/crop-cycles/${id}/reopen`, 'Error reabriendo el ciclo', {
    method: 'POST',
  }))

export const deleteCycle = async (id: number): Promise<void> => {
  await request(`/crop-cycles/delete/${id}`, 'Error eliminando el ciclo', { method: 'DELETE' })
}
