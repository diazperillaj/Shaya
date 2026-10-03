import type {
  CompositionHarvest,
  Drying,
  DryingCompletePayload,
  DryingMethod,
  DryingTrace,
  QualityEval,
  QualityEvalPayload,
  QualityStage,
  TraceCycle,
  WetProcessing,
  WetProcessingStages,
} from '../models/types'
import { request, toNumber, withNumbers } from './http'

/* Beneficio, secado, calidad y trazabilidad */

type Raw = Record<string, unknown>

const WET_DECIMALS = ['floats_kg', 'ambient_temp_c', 'washed_kg', 'cherry_kg', 'fermentation_hours', 'washed_kg_dried']
const DRYING_DECIMALS = ['final_humidity_pct', 'output_kg', 'wet_kg', 'cherry_kg_traced', 'yield_pct']
const QUALITY_DECIMALS = [
  'ripe_pct', 'green_pct', 'overripe_pct', 'bored_pct', 'humidity_pct', 'defects_pct', 'yield_factor', 'score',
]

const mapWet = (raw: Raw): WetProcessing => ({
  ...withNumbers<WetProcessing>(raw, WET_DECIMALS),
  inputs: (raw.inputs as Raw[]).map((input) => withNumbers<WetProcessing['inputs'][number]>(input, ['cherry_kg'])),
})

const mapComposition = (plot: Raw) => ({
  ...withNumbers<Drying['composition'][number]>(plot, ['cherry_kg', 'share_pct']),
  harvests: ((plot.harvests as Raw[]) ?? []).map((harvest) => withNumbers<CompositionHarvest>(harvest, ['cherry_kg'])),
})

const mapDrying = (raw: Raw): Drying => ({
  ...withNumbers<Drying>(raw, DRYING_DECIMALS),
  humidity_range: (raw.humidity_range as (string | null)[]).map(toNumber) as Drying['humidity_range'],
  inputs: (raw.inputs as Raw[]).map((input) => withNumbers<Drying['inputs'][number]>(input, ['wet_kg', 'washed_kg'])),
  humidity_checks: (raw.humidity_checks as Raw[]).map((check) => withNumbers<Drying['humidity_checks'][number]>(check, ['humidity_pct'])),
  composition: (raw.composition as Raw[]).map(mapComposition),
})

/* ── Beneficio ─────────────────────────────────────────────────────────── */

export const fetchWetProcessings = async (farmId: number): Promise<WetProcessing[]> =>
  (await request<Raw[]>('/wet-processings/get', 'Error obteniendo los beneficios', { query: { farm_id: farmId } }))
    .map(mapWet)

export const fetchWetProcessing = async (id: number): Promise<WetProcessing> =>
  mapWet(await request<Raw>(`/wet-processings/get/${id}`, 'Error obteniendo el beneficio'))

export const createWetProcessing = async (
  farmId: number,
  inputs: { harvest_id: number; cherry_kg: number }[],
): Promise<WetProcessing> =>
  mapWet(await request<Raw>('/wet-processings/create', 'Error creando el beneficio', {
    method: 'POST',
    body: { farm_id: farmId, inputs },
  }))

export const updateWetProcessing = async (id: number, stages: WetProcessingStages): Promise<WetProcessing> =>
  mapWet(await request<Raw>(`/wet-processings/update/${id}`, 'Error guardando el beneficio', {
    method: 'PUT',
    body: stages,
  }))

export const replaceWetInputs = async (
  id: number,
  inputs: { harvest_id: number; cherry_kg: number }[],
): Promise<WetProcessing> =>
  mapWet(await request<Raw>(`/wet-processings/${id}/inputs`, 'Error cambiando los aportes', {
    method: 'PUT',
    body: { inputs },
  }))

export const completeWetProcessing = async (id: number, washedKg: number | null): Promise<WetProcessing> =>
  mapWet(await request<Raw>(`/wet-processings/${id}/complete`, 'Error completando el beneficio', {
    method: 'POST',
    body: { washed_kg: washedKg },
  }))

export const reopenWetProcessing = async (id: number): Promise<WetProcessing> =>
  mapWet(await request<Raw>(`/wet-processings/${id}/reopen`, 'Error reabriendo el beneficio', { method: 'POST' }))

export const deleteWetProcessing = async (id: number): Promise<void> => {
  await request(`/wet-processings/delete/${id}`, 'Error eliminando el beneficio', { method: 'DELETE' })
}

/* ── Secado ────────────────────────────────────────────────────────────── */

export const fetchDryings = async (farmId: number): Promise<Drying[]> =>
  (await request<Raw[]>('/dryings/get', 'Error obteniendo los secados', { query: { farm_id: farmId } })).map(mapDrying)

export const fetchDrying = async (id: number): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/get/${id}`, 'Error obteniendo el secado'))

export interface DryingFieldsPayload {
  method: DryingMethod
  other_detail: string | null
  start_date: string
  observations: string | null
}

export const createDrying = async (
  farmId: number,
  fields: DryingFieldsPayload,
  inputs: { wet_processing_id: number; wet_kg: number }[],
): Promise<Drying> =>
  mapDrying(await request<Raw>('/dryings/create', 'Error creando el secado', {
    method: 'POST',
    body: { ...fields, farm_id: farmId, inputs },
  }))

export const updateDrying = async (id: number, fields: DryingFieldsPayload): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/update/${id}`, 'Error guardando el secado', { method: 'PUT', body: fields }))

export const addHumidityCheck = async (
  id: number,
  payload: { check_date: string; humidity_pct: number },
): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/${id}/humidity-checks/create`, 'Error registrando la medición', {
    method: 'POST',
    body: payload,
  }))

export const deleteHumidityCheck = async (checkId: number): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/humidity-checks/delete/${checkId}`, 'Error eliminando la medición', {
    method: 'DELETE',
  }))

export const completeDrying = async (id: number, payload: DryingCompletePayload): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/${id}/complete`, 'Error cerrando el secado', { method: 'POST', body: payload }))

export const sendDryingToInventory = async (
  id: number,
  payload: { full_price: number; purchase_date: string },
): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/${id}/to-inventory`, 'Error enviando al inventario', {
    method: 'POST',
    body: payload,
  }))

export const reopenDrying = async (id: number): Promise<Drying> =>
  mapDrying(await request<Raw>(`/dryings/${id}/reopen`, 'Error reabriendo el secado', { method: 'POST' }))

export const deleteDrying = async (id: number): Promise<void> => {
  await request(`/dryings/delete/${id}`, 'Error eliminando el secado', { method: 'DELETE' })
}

/* ── Calidad ───────────────────────────────────────────────────────────── */

export const fetchQualityEvals = async (
  filter: { harvest_id: number } | { drying_id: number },
): Promise<QualityEval[]> =>
  (await request<Raw[]>('/quality-evals/get', 'Error obteniendo las evaluaciones', { query: filter }))
    .map((raw) => withNumbers<QualityEval>(raw, QUALITY_DECIMALS))

export const createQualityEval = async (
  stage: QualityStage,
  target: { harvest_id: number } | { drying_id: number },
  payload: QualityEvalPayload,
): Promise<QualityEval> =>
  withNumbers(
    await request('/quality-evals/create', 'Error registrando la evaluación', {
      method: 'POST',
      body: { ...payload, ...target, stage },
    }),
    QUALITY_DECIMALS,
  )

export const updateQualityEval = async (id: number, payload: QualityEvalPayload): Promise<QualityEval> =>
  withNumbers(
    await request(`/quality-evals/update/${id}`, 'Error actualizando la evaluación', { method: 'PUT', body: payload }),
    QUALITY_DECIMALS,
  )

export const deleteQualityEval = async (id: number): Promise<void> => {
  await request(`/quality-evals/delete/${id}`, 'Error eliminando la evaluación', { method: 'DELETE' })
}

/* ── Trazabilidad ──────────────────────────────────────────────────────── */

const mapTrace = (raw: Raw): DryingTrace => ({
  drying: mapDrying(raw.drying as Raw),
  plots: (raw.plots as Raw[]).map((plot) => ({
    ...withNumbers<DryingTrace['plots'][number]>(plot, ['cherry_kg', 'share_pct']),
    cycles: (plot.cycles as Raw[]).map((cycle) => ({
      ...withNumbers<DryingTrace['plots'][number]['cycles'][number]>(cycle, ['cherry_kg']),
      harvests: (cycle.harvests as Raw[]).map((harvest) => withNumbers<TraceCycle['harvests'][number]>(harvest, ['cherry_kg'])),
      labors: (cycle.labors as Raw[]).map((labor) => withNumbers<TraceCycle['labors'][number]>(labor, ['total_cost'])),
    })),
  })),
  wet_processings: (raw.wet_processings as Raw[]).map((wet) =>
    withNumbers<DryingTrace['wet_processings'][number]>(wet, ['cherry_kg', 'washed_kg', 'wet_kg']),
  ),
})

export const fetchDryingTrace = async (dryingId: number): Promise<DryingTrace> =>
  mapTrace(await request<Raw>(`/traceability/dryings/${dryingId}`, 'Error obteniendo la trazabilidad'))

export const fetchParchmentTrace = async (parchmentId: number): Promise<DryingTrace> =>
  mapTrace(await request<Raw>(`/traceability/parchments/${parchmentId}`, 'Error obteniendo la trazabilidad'))
