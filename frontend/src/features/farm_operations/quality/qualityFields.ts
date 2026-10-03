import type { QualityEval, QualityStage } from '../models/types'

/** Resultados de cada etapa, con su etiqueta (la broca aplica a ambas) */
export const QUALITY_FIELDS: Record<QualityStage, { key: QualityResult; label: string; unit: string }[]> = {
  cherry: [
    { key: 'ripe_pct', label: 'Maduros', unit: '%' },
    { key: 'green_pct', label: 'Verdes', unit: '%' },
    { key: 'overripe_pct', label: 'Sobremaduros o secos', unit: '%' },
    { key: 'bored_pct', label: 'Brocados', unit: '%' },
  ],
  parchment: [
    { key: 'humidity_pct', label: 'Humedad', unit: '%' },
    { key: 'defects_pct', label: 'Defectos', unit: '%' },
    { key: 'yield_factor', label: 'Factor de rendimiento', unit: '' },
    { key: 'score', label: 'Puntaje (0–100)', unit: 'pts' },
    { key: 'bored_pct', label: 'Brocados', unit: '%' },
  ],
}

export const QUALITY_RESULTS = [
  'ripe_pct', 'green_pct', 'overripe_pct', 'bored_pct', 'humidity_pct', 'defects_pct', 'yield_factor', 'score',
] as const satisfies readonly (keyof QualityEval)[]

export type QualityResult = (typeof QUALITY_RESULTS)[number]
