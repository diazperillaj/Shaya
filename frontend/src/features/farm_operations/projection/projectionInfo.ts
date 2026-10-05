import { fmtNumber } from '../format'
import type { ProjectionStage, QualityProjection } from '../models/types'

/* Presentación de la proyección de calidad (generador-sintetico-ml §6) */

export const STAGES: { id: ProjectionStage; label: string }[] = [
  { id: 'pre', label: 'Antes de cosechar' },
  { id: 'harvest', label: 'Cosecha' },
  { id: 'wet', label: 'Beneficio' },
  { id: 'drying', label: 'Secado' },
]

export const YIELD_FACTOR_HINT = 'kg de pergamino seco por 70 kg de excelso; menor es mejor'

export const fmtScore = (p: QualityProjection) => fmtNumber(p.score, 1)
export const fmtDefects = (p: QualityProjection) => fmtNumber(p.defects_pct, 1, '%')
export const fmtYieldFactor = (p: QualityProjection) => fmtNumber(p.yield_factor, 1)
export const fmtCompleteness = (p: QualityProjection) => `${Math.round(p.completeness * 100)} %`
