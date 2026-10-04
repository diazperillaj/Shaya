import { CalendarRange } from 'lucide-react'
import { fmtDate } from '../format'
import type { Season } from '../models/types'
import { PRESETS, resolvePreset, type PeriodChoice } from './period'

/**
 * Periodo del dashboard: botones rápidos (calendario y cosechas) y rango
 * personalizado. Solo los widgets de periodo lo obedecen; las alertas y los
 * de estado muestran siempre el ahora.
 */
export default function PeriodPicker({
  value,
  seasons,
  today,
  onChange,
}: {
  value: PeriodChoice
  seasons: Season[]
  today: string
  onChange: (choice: PeriodChoice) => void
}) {
  const pick = (preset: PeriodChoice['preset']) => {
    const range = resolvePreset(preset, seasons, today)
    if (range) onChange({ preset, ...range })
  }
  const custom = (field: 'from' | 'to', date: string) => {
    if (!date) return
    const next = { ...value, preset: 'custom' as const, [field]: date }
    if (next.from <= next.to) onChange(next)
  }
  const season = value.preset.startsWith('season') ? seasons[Number(value.preset.slice(-1)) - 1] : null

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map(({ id, label, seasons: needed }) => {
          const disabled = needed !== undefined && seasons.length === 0
          const active = value.preset === id
          return (
            <button
              key={id}
              type="button"
              disabled={disabled}
              onClick={() => pick(id)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-40 ${
                active ? 'bg-emerald-900 text-white' : 'bg-gray-100 text-gray-700 hover:bg-emerald-50 hover:text-emerald-900'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>
      <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600">
        <CalendarRange className="h-4 w-4 text-emerald-800" />
        <label className="flex items-center gap-1.5">
          Desde
          <input
            type="date"
            value={value.from}
            max={value.to}
            onChange={(e) => custom('from', e.target.value)}
            className="rounded-lg border border-gray-200 px-2 py-1 text-sm"
          />
        </label>
        <label className="flex items-center gap-1.5">
          hasta
          <input
            type="date"
            value={value.to}
            min={value.from}
            max={today}
            onChange={(e) => custom('to', e.target.value)}
            className="rounded-lg border border-gray-200 px-2 py-1 text-sm"
          />
        </label>
        {season && value.preset === 'season1' && (
          <span className="text-xs text-gray-400">
            {season.label} · {season.harvests} pasadas{season.open ? ' · en curso' : ''}
          </span>
        )}
        {value.preset !== 'season1' && (
          <span className="text-xs text-gray-400">
            {fmtDate(value.from)} – {fmtDate(value.to)}
          </span>
        )}
      </div>
    </div>
  )
}
