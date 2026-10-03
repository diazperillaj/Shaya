import { KG_PER_ARROBA } from '../models/labels'

/**
 * Pesos en kg o en arrobas (decisión F1): la API solo habla en kg y la
 * conversión es solo de entrada.
 */
export type WeightUnit = 'kg' | 'arroba'

export const WEIGHT_UNIT_LABELS: Record<WeightUnit, string> = { kg: 'kg', arroba: '@' }

/** Texto del formulario en la unidad elegida → kg con tres decimales (vacío → null) */
export const toKg = (value: string, unit: WeightUnit): number | null => {
  if (value.trim() === '') return null
  const kg = Number(value) * (unit === 'arroba' ? KG_PER_ARROBA : 1)
  return Math.round(kg * 1000) / 1000
}

/** kg → cantidad en la unidad dada, con tres decimales */
export const fromKg = (kg: number, unit: WeightUnit): number =>
  Math.round((unit === 'arroba' ? kg / KG_PER_ARROBA : kg) * 1000) / 1000
