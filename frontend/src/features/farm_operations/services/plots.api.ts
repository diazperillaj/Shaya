import type {
  Plot,
  PlotCreatePayload,
  PlotEvent,
  PlotEventPayload,
  PlotFields,
  QualityProjection,
  RenewalDefaults,
} from '../models/types'
import { request, toNumber } from './http'

/** Campos decimales del lote, que la API envía como texto */
type DecimalField =
  | 'area' | 'slope' | 'initial_age_years' | 'row_spacing_m'
  | 'plant_spacing_m' | 'seed_cost' | 'effective_age_years'

type PlotApi = Omit<Plot, DecimalField> & Record<DecimalField, string | null>

const mapPlot = (plot: PlotApi): Plot => ({
  ...plot,
  area: toNumber(plot.area),
  slope: toNumber(plot.slope),
  initial_age_years: toNumber(plot.initial_age_years),
  row_spacing_m: toNumber(plot.row_spacing_m),
  plant_spacing_m: toNumber(plot.plant_spacing_m),
  seed_cost: toNumber(plot.seed_cost),
  effective_age_years: toNumber(plot.effective_age_years) ?? 0,
})

export const fetchPlots = async (farmId: number): Promise<Plot[]> => {
  const plots = await request<PlotApi[]>('/plots/get', 'Error obteniendo los lotes', {
    query: { farm_id: farmId },
  })
  return plots.map(mapPlot)
}

export const fetchPlot = async (id: number): Promise<Plot> =>
  mapPlot(await request<PlotApi>(`/plots/get/${id}`, 'Error obteniendo el lote'))

export const fetchRenewalDefaults = async (id: number): Promise<RenewalDefaults> => {
  const defaults = await request<RenewalDefaults & { area: string | null; slope: string | null }>(
    `/plots/get/${id}/renewal-defaults`,
    'Error obteniendo los datos del terreno',
  )
  return { ...defaults, area: toNumber(defaults.area), slope: toNumber(defaults.slope) }
}

export const createPlot = async (payload: PlotCreatePayload): Promise<Plot> =>
  mapPlot(await request<PlotApi>('/plots/create', 'Error creando el lote', {
    method: 'POST',
    body: payload,
  }))

export const updatePlot = async (id: number, payload: PlotFields): Promise<Plot> =>
  mapPlot(await request<PlotApi>(`/plots/update/${id}`, 'Error actualizando el lote', {
    method: 'PUT',
    body: payload,
  }))

export const closePlot = async (
  id: number,
  payload: { closed_at: string; description: string | null },
): Promise<Plot> =>
  mapPlot(await request<PlotApi>(`/plots/${id}/close`, 'Error cerrando el lote', {
    method: 'POST',
    body: payload,
  }))

export const reopenPlot = async (id: number, payload: { description: string | null }): Promise<Plot> =>
  mapPlot(await request<PlotApi>(`/plots/${id}/reopen`, 'Error reabriendo el lote', {
    method: 'POST',
    body: payload,
  }))

export const deletePlot = async (id: number): Promise<void> => {
  await request(`/plots/delete/${id}`, 'Error eliminando el lote', { method: 'DELETE' })
}

export const fetchPlotEvents = async (id: number): Promise<PlotEvent[]> =>
  request<PlotEvent[]>(`/plots/${id}/events/get`, 'Error obteniendo el historial del lote')

export const createPlotEvent = async (id: number, payload: PlotEventPayload): Promise<PlotEvent> =>
  request<PlotEvent>(`/plots/${id}/events/create`, 'Error registrando el evento', {
    method: 'POST',
    body: payload,
  })

export const fetchQualityProjection = (id: number): Promise<QualityProjection> =>
  request(`/plots/${id}/quality-projection`, 'Error obteniendo la proyección de calidad')
