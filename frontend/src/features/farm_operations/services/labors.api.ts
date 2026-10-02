import type { LaborKind, LaborPayload, LaborRecords } from '../models/types'
import { request, toNumber } from './http'

/** Campos decimales de cada labor, que la API envía como texto */
const DECIMAL_FIELDS: Record<LaborKind, string[]> = {
  fertilizations: ['quantity', 'dose_per_tree_g', 'cost'],
  'phytosanitary-apps': ['quantity', 'cost'],
  irrigations: ['volume_liters'],
  'pest-monitorings': ['broca_pct', 'roya_pct', 'other_pest_pct'],
  'cultural-practices': ['cost'],
  'flowering-records': [],
}

type RawRecord = Record<string, unknown>

const mapRecord = <K extends LaborKind>(kind: K, raw: RawRecord): LaborRecords[K] => {
  const record = { ...raw }
  DECIMAL_FIELDS[kind].forEach((field) => {
    record[field] = toNumber(record[field] as string | null)
  })
  return record as unknown as LaborRecords[K]
}

/**
 * Labores del ciclo. Las seis comparten las mismas rutas
 * (`/<labor>/create`, `/get`…), así que un solo servicio las atiende.
 */
export const fetchLabors = async <K extends LaborKind>(
  kind: K,
  filters: { crop_cycle_id?: number; plot_id?: number },
): Promise<LaborRecords[K][]> => {
  const records = await request<RawRecord[]>(`/${kind}/get`, 'Error obteniendo las labores', { query: filters })
  return records.map((record) => mapRecord(kind, record))
}

export const createLabor = async <K extends LaborKind>(
  kind: K,
  payload: LaborPayload & { crop_cycle_id: number },
): Promise<LaborRecords[K]> =>
  mapRecord(kind, await request<RawRecord>(`/${kind}/create`, 'Error registrando la labor', {
    method: 'POST',
    body: payload,
  }))

/** La misma labor en varios lotes de una finca: un registro por ciclo, todo o nada */
export const bulkCreateLabor = async <K extends LaborKind>(
  kind: K,
  /** Campos comunes de la labor + `items` con el ciclo y los montos de cada lote */
  payload: { [field: string]: unknown; items: (LaborPayload & { crop_cycle_id: number })[] },
): Promise<LaborRecords[K][]> => {
  const records = await request<RawRecord[]>(`/${kind}/bulk-create`, 'Error registrando la labor', {
    method: 'POST',
    body: payload,
  })
  return records.map((record) => mapRecord(kind, record))
}

export const updateLabor = async <K extends LaborKind>(
  kind: K,
  id: number,
  payload: LaborPayload,
): Promise<LaborRecords[K]> =>
  mapRecord(kind, await request<RawRecord>(`/${kind}/update/${id}`, 'Error actualizando la labor', {
    method: 'PUT',
    body: payload,
  }))

export const deleteLabor = async (kind: LaborKind, id: number): Promise<void> => {
  await request(`/${kind}/delete/${id}`, 'Error eliminando la labor', { method: 'DELETE' })
}
