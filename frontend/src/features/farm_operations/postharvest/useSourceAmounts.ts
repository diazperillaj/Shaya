import { useState } from 'react'
import { fromKg, toKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'

/**
 * Estado de una mezcla: cuánto aporta cada origen elegido, escrito en kg o
 * en arrobas. Al cambiar de unidad se convierten las cantidades escritas.
 */
export function useSourceAmounts(initial: Record<number, number> = {}) {
  const [unit, setUnit] = useState<WeightUnit>('kg')
  const [amounts, setAmounts] = useState<Record<number, string>>(
    Object.fromEntries(Object.entries(initial).map(([id, kg]) => [id, String(kg)])),
  )

  const change = (id: number, value: string | undefined) =>
    setAmounts((current) => {
      const next = { ...current }
      if (value === undefined) delete next[id]
      else next[id] = value
      return next
    })

  const changeUnit = (next: WeightUnit) => {
    if (next === unit) return
    setAmounts((current) =>
      Object.fromEntries(
        Object.entries(current).map(([id, value]) => {
          const kg = toKg(value, unit)
          return [id, kg === null ? value : String(fromKg(kg, next))]
        }),
      ),
    )
    setUnit(next)
  }

  /** Orígenes elegidos con sus kg; `null` si falta alguna cantidad válida */
  const entries = (): { id: number; kg: number }[] | null => {
    const result = Object.entries(amounts).map(([id, value]) => ({ id: Number(id), kg: toKg(value, unit) }))
    return result.every((item) => item.kg !== null && item.kg > 0) ? (result as { id: number; kg: number }[]) : null
  }

  return { amounts, unit, change, changeUnit, entries }
}
