/**
 * Datos y estilos compartidos de las gráficas (Recharts).
 *
 * Los dashboards reciben del backend el contrato `BarChartData`
 * (`{labels, series: [{name, data}]}`) y lo convierten aquí a la forma que
 * espera Recharts: un punto por etiqueta con un valor por serie.
 */

export interface ChartSeriesApi {
  name: string
  data: number[]
}

export interface BarChartDataApi {
  labels: string[]
  series: ChartSeriesApi[]
}

// Each entry: { name: label, [seriesName]: value, ... }
export type RechartsDataPoint = Record<string, string | number>

export interface RechartsChart {
  data: RechartsDataPoint[]
  keys: string[] // series names → used as <Bar dataKey="..." />
}

export function toRecharts(chart: BarChartDataApi): RechartsChart {
  const data: RechartsDataPoint[] = chart.labels.map((label, i) => {
    const point: RechartsDataPoint = { name: label }
    for (const series of chart.series) {
      point[series.name] = series.data[i] ?? 0
    }
    return point
  })
  return { data, keys: chart.series.map((s) => s.name) }
}

export const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

// Gradient IDs for vertical bars (top → bottom) and horizontal bars (left → right)
export const GRAD_V = ['url(#gv0)', 'url(#gv1)', 'url(#gv2)', 'url(#gv3)']
export const GRAD_H = ['url(#gh0)', 'url(#gh1)', 'url(#gh2)', 'url(#gh3)']

// Palette for pie/donut slices
export const PIE_COLORS = [
  '#065f46', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0',
  '#0d9488', '#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4',
  '#047857', '#059669', '#0f766e',
]
