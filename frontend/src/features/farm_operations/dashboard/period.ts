import type { Season } from '../models/types'

/**
 * Periodo del dashboard (dashboards-alertas §2.1).
 *
 * Los botones de calendario se resuelven aquí; los de cosecha toman las
 * temporadas que calcula el backend (`/dashboard/periods`), sin repetir su
 * lógica. El último periodo elegido se recuerda por navegador.
 */

export type PresetId = 'month' | 'm3' | 'm6' | 'year' | 'season1' | 'season2' | 'season3' | 'all' | 'custom'

export interface PeriodChoice {
  preset: PresetId
  from: string
  to: string
}

export const PRESETS: { id: Exclude<PresetId, 'custom'>; label: string; seasons?: number }[] = [
  { id: 'month', label: 'Este mes' },
  { id: 'm3', label: 'Últimos 3 meses' },
  { id: 'm6', label: 'Últimos 6 meses' },
  { id: 'year', label: 'Último año' },
  { id: 'season1', label: 'Última cosecha', seasons: 1 },
  { id: 'season2', label: 'Últimas 2 cosechas', seasons: 2 },
  { id: 'season3', label: 'Últimas 3 cosechas', seasons: 3 },
  { id: 'all', label: 'Todo' },
]

const STORAGE_KEY = 'farm-dashboard-period'

const pad = (n: number) => String(n).padStart(2, '0')
const iso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const parse = (value: string) => new Date(`${value}T00:00:00`)

function shiftDays(value: string, days: number): string {
  const d = parse(value)
  d.setDate(d.getDate() + days)
  return iso(d)
}

function shiftMonths(value: string, months: number): string {
  const d = parse(value)
  d.setMonth(d.getMonth() + months)
  return iso(d)
}

/** Rango de un botón rápido; los de cosecha necesitan las temporadas (null mientras no haya) */
export function resolvePreset(preset: PresetId, seasons: Season[], today: string): { from: string; to: string } | null {
  switch (preset) {
    case 'month':
      return { from: `${today.slice(0, 8)}01`, to: today }
    case 'm3':
      return { from: shiftDays(shiftMonths(today, -3), 1), to: today }
    case 'm6':
      return { from: shiftDays(shiftMonths(today, -6), 1), to: today }
    case 'year':
      return { from: shiftDays(today, -364), to: today }   // el mismo que el backend por defecto
    case 'season1':
    case 'season2':
    case 'season3': {
      const count = Number(preset.slice(-1))
      if (seasons.length === 0) return null
      const oldest = seasons[Math.min(count, seasons.length) - 1]
      return { from: oldest.date_from, to: seasons[0].date_to }
    }
    case 'all':
      return { from: seasons.at(-1)?.date_from ?? '2000-01-01', to: today }
    default:
      return null
  }
}

export function loadChoice(): PeriodChoice | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PeriodChoice) : null
  } catch {
    return null
  }
}

export function saveChoice(choice: PeriodChoice): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(choice))
  } catch {
    // Sin almacenamiento local (navegación privada): el periodo no se recuerda
  }
}
