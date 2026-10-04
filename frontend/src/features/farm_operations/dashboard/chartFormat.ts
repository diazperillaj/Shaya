import { fmtMoney, fmtNumber } from '../format'

/** Formatos de los valores de las gráficas del dashboard */
export const asKg = (value: number) => fmtNumber(value, 0, 'kg')
export const asPct = (value: number) => `${fmtNumber(value, 1)} %`
export const asScore = (value: number) => fmtNumber(value, 1)
export const asCount = (value: number) => fmtNumber(value, 0)
export const asCop = (value: number) => fmtMoney(value)

/**
 * ¿La barra del histograma de humedad cae dentro del rango de la finca?
 * Las etiquetas vienen del backend: «< 8», «10–10,5», «≥ 14».
 */
export function humidityBinInside(label: string, range: [number | null, number | null]): boolean {
  const [low, high] = range
  const bounds = label.match(/^(\d+(?:,\d+)?)–(\d+(?:,\d+)?)$/)
  if (!bounds || low === null || high === null) return false
  const [from, to] = [bounds[1], bounds[2]].map((n) => Number(n.replace(',', '.')))
  return from >= low && to <= high
}

export const unitName = (unit: 'farm' | 'plot', pluralForm = false) =>
  unit === 'plot' ? (pluralForm ? 'lotes' : 'lote') : pluralForm ? 'fincas' : 'finca'
