import { useState } from 'react'
import type { Plot } from '../models/types'
import type { AmountField, AmountInfo } from './laborConfig'
import { splitByArea } from './split'

type Amounts = Partial<Record<AmountField, string>>
const NO_TOTALS: Record<AmountField, string> = { quantity: '', cost: '', volume_liters: '' }

/**
 * Estado del registro en varios lotes: qué lotes se eligen, los totales y
 * el reparto por lote. El reparto sale de los totales (por área); lo que el
 * usuario corrige en un lote se respeta hasta que cambie un total o la
 * selección, que vuelven a repartir.
 */
export function usePlotDistribution(amounts: AmountInfo[], initialPicked: number[]) {
  const [picked, setPicked] = useState<number[]>(initialPicked)
  const [totals, setTotals] = useState(NO_TOTALS)
  const [overrides, setOverrides] = useState<Record<number, Amounts>>({})

  /** Reparto entre los lotes que reciben la labor */
  const forPlots = (plots: Plot[]) => {
    const split = Object.fromEntries(
      amounts.map(({ field, decimals }) => [
        field,
        totals[field].trim() === '' ? null : splitByArea(Number(totals[field]), plots, decimals),
      ]),
    ) as Record<AmountField, Record<number, number> | null>

    const rowValue = (plotId: number, field: AmountField): string => {
      const own = overrides[plotId]?.[field]
      if (own !== undefined) return own
      const share = split[field]?.[plotId]
      return share === undefined ? '' : String(share)
    }
    const rowAmounts = (plotId: number): Amounts =>
      Object.fromEntries(amounts.map(({ field }) => [field, rowValue(plotId, field)]))

    return { rowValue, rowAmounts }
  }

  return {
    picked,
    totals,
    forPlots,
    toggle: (plotId: number) => {
      setPicked((current) => (current.includes(plotId) ? current.filter((id) => id !== plotId) : [...current, plotId]))
      setOverrides({})
    },
    setTotal: (field: AmountField, value: string) => {
      setTotals((current) => ({ ...current, [field]: value }))
      setOverrides({})
    },
    setRow: (plotId: number, field: AmountField, value: string) =>
      setOverrides((current) => ({ ...current, [plotId]: { ...current[plotId], [field]: value } })),
    /** Vuelve a repartir desde los totales (p. ej. al cambiar de alcance) */
    resetSplit: () => setOverrides({}),
  }
}
