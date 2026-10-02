import type { SoilAnalysis, SoilAnalysisPayload } from '../models/types'
import { request, toNumber } from './http'

type DecimalField = 'ph' | 'organic_matter_pct' | 'nitrogen' | 'phosphorus' | 'potassium'
type SoilApi = Omit<SoilAnalysis, DecimalField> & Record<DecimalField, string | null>

const mapAnalysis = (analysis: SoilApi): SoilAnalysis => ({
  ...analysis,
  ph: toNumber(analysis.ph),
  organic_matter_pct: toNumber(analysis.organic_matter_pct),
  nitrogen: toNumber(analysis.nitrogen),
  phosphorus: toNumber(analysis.phosphorus),
  potassium: toNumber(analysis.potassium),
})

export const fetchSoilAnalyses = async (plotId: number): Promise<SoilAnalysis[]> => {
  const analyses = await request<SoilApi[]>('/soil-analyses/get', 'Error obteniendo los análisis de suelo', {
    query: { plot_id: plotId },
  })
  return analyses.map(mapAnalysis)
}

export const createSoilAnalysis = async (plotId: number, payload: SoilAnalysisPayload): Promise<SoilAnalysis> =>
  mapAnalysis(await request<SoilApi>('/soil-analyses/create', 'Error registrando el análisis', {
    method: 'POST',
    body: { ...payload, plot_id: plotId },
  }))

export const updateSoilAnalysis = async (id: number, payload: SoilAnalysisPayload): Promise<SoilAnalysis> =>
  mapAnalysis(await request<SoilApi>(`/soil-analyses/update/${id}`, 'Error actualizando el análisis', {
    method: 'PUT',
    body: payload,
  }))

export const deleteSoilAnalysis = async (id: number): Promise<void> => {
  await request(`/soil-analyses/delete/${id}`, 'Error eliminando el análisis', { method: 'DELETE' })
}
