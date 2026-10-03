import { inputClass } from '../components/styles'
import { WEIGHT_UNIT_LABELS, fromKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { fmtNumber } from '../format'

/** Un origen de café para una mezcla: una cosecha o un beneficio */
export interface Source {
  id: number
  title: string
  detail: string
  /** Kg disponibles; `null` = sin tope todavía (cosecha abierta) */
  available: number | null
}

/**
 * Lista de orígenes para armar una mezcla: se marca cada uno y se indica
 * cuánto aporta, en kg o en arrobas. Al marcarlo se propone lo disponible.
 */
export default function SourceRows({
  sources,
  amounts,
  onChange,
  unit,
  onUnitChange,
  emptyText,
}: {
  sources: Source[]
  /** Cantidad escrita por origen, en la unidad elegida; sin clave = no elegido */
  amounts: Record<number, string>
  onChange: (id: number, value: string | undefined) => void
  unit: WeightUnit
  onUnitChange: (unit: WeightUnit) => void
  emptyText: string
}) {
  if (sources.length === 0) return <p className="text-sm text-amber-800">{emptyText}</p>

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-end gap-2 text-xs text-gray-500">
        Cantidades en
        <div className="flex rounded-lg bg-gray-100 p-0.5" role="radiogroup" aria-label="Unidad">
          {(Object.keys(WEIGHT_UNIT_LABELS) as WeightUnit[]).map((option) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={unit === option}
              onClick={() => onUnitChange(option)}
              className={`rounded-md px-2.5 py-1 font-medium ${unit === option ? 'bg-white text-emerald-900 shadow-sm' : ''}`}
            >
              {WEIGHT_UNIT_LABELS[option]}
            </button>
          ))}
        </div>
      </div>
      <ul className="divide-y divide-gray-100 rounded-xl border border-gray-100">
        {sources.map((source) => {
          const chosen = source.id in amounts
          return (
            <li key={source.id} className="flex flex-wrap items-center justify-between gap-3 px-3 py-2.5">
              <label className="flex cursor-pointer items-start gap-3">
                <input
                  type="checkbox"
                  checked={chosen}
                  onChange={(e) =>
                    onChange(
                      source.id,
                      e.target.checked
                        ? source.available !== null && source.available > 0
                          ? String(fromKg(source.available, unit))
                          : ''
                        : undefined,
                    )
                  }
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 accent-emerald-800"
                />
                <span>
                  <span className="block text-sm text-gray-900">{source.title}</span>
                  <span className="block text-xs text-gray-500">
                    {source.detail} ·{' '}
                    {source.available === null
                      ? 'sin tope hasta cerrarla'
                      : `disponible ${fmtNumber(source.available, 3, 'kg')}`}
                  </span>
                </span>
              </label>
              {chosen && (
                <div className="w-32">
                  <input
                    type="number"
                    inputMode="decimal"
                    step="0.001"
                    min="0"
                    aria-label={`Cantidad de ${source.title}`}
                    value={amounts[source.id]}
                    onChange={(e) => onChange(source.id, e.target.value)}
                    className={`${inputClass()} py-1.5`}
                  />
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
