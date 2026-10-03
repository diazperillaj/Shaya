import type {
  Harvest,
  HarvestDetail,
  HarvestPayload,
  HarvestUpdatePayload,
  HarvestWork,
  HarvestWorkPayload,
} from '../models/types'
import { request, toNumber } from './http'

type HarvestDecimal =
  | 'rate_per_kg' | 'rate_per_day' | 'total_cherry_kg' | 'kg_registered' | 'value_total' | 'value_pending'
type WorkDecimal = 'kg_collected' | 'rate_per_kg' | 'day_value' | 'total_value'

type HarvestApi = Omit<Harvest, HarvestDecimal> & Record<HarvestDecimal, string | null>
type WorkApi = Omit<HarvestWork, WorkDecimal> & Record<WorkDecimal, string | null>
type DetailApi = HarvestApi & { works: WorkApi[] }

export const mapWork = (work: WorkApi): HarvestWork => ({
  ...work,
  kg_collected: toNumber(work.kg_collected),
  rate_per_kg: toNumber(work.rate_per_kg),
  day_value: toNumber(work.day_value),
  total_value: toNumber(work.total_value) ?? 0,
})

const mapHarvest = (harvest: HarvestApi): Harvest => ({
  ...harvest,
  rate_per_kg: toNumber(harvest.rate_per_kg),
  rate_per_day: toNumber(harvest.rate_per_day),
  total_cherry_kg: toNumber(harvest.total_cherry_kg),
  kg_registered: toNumber(harvest.kg_registered) ?? 0,
  value_total: toNumber(harvest.value_total) ?? 0,
  value_pending: toNumber(harvest.value_pending) ?? 0,
})

const mapDetail = ({ works, ...harvest }: DetailApi): HarvestDetail => ({
  ...mapHarvest(harvest),
  works: works.map(mapWork),
})

/** Pasadas de cosecha de un ciclo, de la más reciente a la más antigua */
export const fetchHarvests = async (cycleId: number): Promise<Harvest[]> => {
  const harvests = await request<HarvestApi[]>('/harvests/get', 'Error obteniendo las cosechas', {
    query: { crop_cycle_id: cycleId },
  })
  return harvests.map(mapHarvest)
}

export const fetchHarvest = async (id: number): Promise<HarvestDetail> =>
  mapDetail(await request<DetailApi>(`/harvests/get/${id}`, 'Error obteniendo la cosecha'))

export const createHarvest = async (cycleId: number, payload: HarvestPayload): Promise<HarvestDetail> =>
  mapDetail(await request<DetailApi>('/harvests/create', 'Error abriendo la cosecha', {
    method: 'POST',
    body: { ...payload, crop_cycle_id: cycleId },
  }))

export const updateHarvest = async (id: number, payload: HarvestUpdatePayload): Promise<HarvestDetail> =>
  mapDetail(await request<DetailApi>(`/harvests/update/${id}`, 'Error actualizando la cosecha', {
    method: 'PUT',
    body: payload,
  }))

export const closeHarvest = async (
  id: number,
  payload: { end_date: string; total_cherry_kg: number | null },
): Promise<HarvestDetail> =>
  mapDetail(await request<DetailApi>(`/harvests/${id}/close`, 'Error cerrando la cosecha', {
    method: 'POST',
    body: payload,
  }))

export const reopenHarvest = async (id: number): Promise<HarvestDetail> =>
  mapDetail(await request<DetailApi>(`/harvests/${id}/reopen`, 'Error reabriendo la cosecha', { method: 'POST' }))

export const deleteHarvest = async (id: number): Promise<void> => {
  await request(`/harvests/delete/${id}`, 'Error eliminando la cosecha', { method: 'DELETE' })
}

export const createHarvestWork = async (harvestId: number, payload: HarvestWorkPayload): Promise<HarvestWork> =>
  mapWork(await request<WorkApi>(`/harvests/${harvestId}/works/create`, 'Error registrando la recolección', {
    method: 'POST',
    body: payload,
  }))

export const updateHarvestWork = async (id: number, payload: HarvestWorkPayload): Promise<HarvestWork> =>
  mapWork(await request<WorkApi>(`/harvests/works/update/${id}`, 'Error actualizando la recolección', {
    method: 'PUT',
    body: payload,
  }))

export const deleteHarvestWork = async (id: number): Promise<void> => {
  await request(`/harvests/works/delete/${id}`, 'Error eliminando la recolección', { method: 'DELETE' })
}
