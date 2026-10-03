import { useId } from 'react'
import { fmtNumber } from '../format'
import { FieldShell } from './fields'
import { inputClass } from './styles'
import { WEIGHT_UNIT_LABELS, fromKg, toKg } from './weight'
import type { WeightUnit } from './weight'

/**
 * Campo de peso que se escribe en kg o en arrobas; muestra la equivalencia
 * en kg cuando se usan arrobas.
 */
export default function WeightField({
  label,
  value,
  unit,
  onChange,
  onUnitChange,
  required,
  error,
  hint,
}: {
  label: string
  value: string
  unit: WeightUnit
  onChange: (value: string) => void
  onUnitChange: (unit: WeightUnit) => void
  required?: boolean
  error?: string
  hint?: string
}) {
  const id = useId()
  const kg = toKg(value, unit)
  const equivalence = unit === 'arroba' && kg !== null ? `= ${fmtNumber(kg, 3, 'kg')}` : undefined

  /** Cambia de unidad conservando la cantidad: 25 kg pasan a 2 @ */
  const switchUnit = (next: WeightUnit) => {
    if (next === unit) return
    if (kg !== null) onChange(String(fromKg(kg, next)))
    onUnitChange(next)
  }

  return (
    <FieldShell id={id} label={label} required={required} error={error} hint={equivalence ?? hint}>
      <div className="flex gap-2">
        <input
          id={id}
          type="number"
          inputMode="decimal"
          step="0.001"
          min="0"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={inputClass(error)}
        />
        <div className="flex rounded-xl bg-gray-100 p-1" role="radiogroup" aria-label="Unidad">
          {(Object.keys(WEIGHT_UNIT_LABELS) as WeightUnit[]).map((option) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={unit === option}
              onClick={() => switchUnit(option)}
              className={`rounded-lg px-3 text-sm font-medium transition ${
                unit === option ? 'bg-white text-emerald-900 shadow-sm' : 'text-gray-500'
              }`}
            >
              {WEIGHT_UNIT_LABELS[option]}
            </button>
          ))}
        </div>
      </div>
    </FieldShell>
  )
}
