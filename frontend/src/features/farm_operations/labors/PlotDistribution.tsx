import { useMemo } from 'react'
import { NumberField } from '../components/fields'
import { inputClass } from '../components/styles'
import { fmtNumber, plural } from '../format'
import type { Plot } from '../models/types'
import type { AmountField, AmountInfo } from './laborConfig'
import { splitsByArea } from './split'

interface PlotDistributionProps {
  scope: 'several' | 'farm'
  /** Lotes activos con ciclo activo: los únicos que pueden recibir la labor */
  eligible: Plot[]
  /** Lotes activos sin ciclo activo */
  withoutCycle: Plot[]
  selected: Plot[]
  onToggle: (plotId: number) => void
  amounts: AmountInfo[]
  /** Unidad del insumo, para la cantidad */
  supplyUnit: string | null
  totals: Record<AmountField, string>
  onTotalChange: (field: AmountField, value: string) => void
  rowValue: (plotId: number, field: AmountField) => string
  onRowChange: (plotId: number, field: AmountField, value: string) => void
  error?: string
}

/** Lotes que reciben la labor y cuánto le toca a cada uno */
export default function PlotDistribution({
  scope,
  eligible,
  withoutCycle,
  selected,
  onToggle,
  amounts,
  supplyUnit,
  totals,
  onTotalChange,
  rowValue,
  onRowChange,
  error,
}: PlotDistributionProps) {
  const unitOf = (amount: AmountInfo) => amount.unit ?? supplyUnit ?? ''
  const selectedIds = useMemo(() => new Set(selected.map((plot) => plot.id)), [selected])

  return (
    <div className="flex flex-col gap-4">
      {eligible.length === 0 ? (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Ningún lote de la finca tiene un ciclo activo. Abre el ciclo de cada lote para registrar sus labores.
        </p>
      ) : scope === 'farm' ? (
        <p className="text-sm text-gray-600">
          Se registra en {plural(eligible.length, 'lote con ciclo activo', 'lotes con ciclo activo')}:{' '}
          <span className="text-gray-900">{eligible.map((plot) => plot.name).join(', ')}</span>.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-1 sm:grid-cols-2">
          {eligible.map((plot) => (
            <li key={plot.id}>
              <label className="flex cursor-pointer items-center gap-3 rounded-lg px-2 py-1.5 text-sm hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={selectedIds.has(plot.id)}
                  onChange={() => onToggle(plot.id)}
                  className="h-4 w-4 rounded border-gray-300 accent-emerald-800"
                />
                <span className="text-gray-900">{plot.name}</span>
                <span className="text-xs text-gray-400">{fmtNumber(plot.area, 2, 'ha')}</span>
              </label>
            </li>
          ))}
        </ul>
      )}
      {withoutCycle.length > 0 && (
        <p className="text-xs text-gray-400">
          Sin ciclo activo (no se incluyen): {withoutCycle.map((plot) => plot.name).join(', ')}.
        </p>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}

      {amounts.length > 0 && selected.length > 0 && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {amounts.map((amount) => (
              <NumberField
                key={amount.field}
                label={`${amount.label} total`}
                required={amount.required}
                unit={unitOf(amount)}
                step={amount.step}
                min="0"
                value={totals[amount.field]}
                onChange={(value) => onTotalChange(amount.field, value)}
              />
            ))}
          </div>

          <div className="overflow-x-auto rounded-xl border border-gray-100">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs text-gray-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Lote</th>
                  {amounts.map((amount) => (
                    <th key={amount.field} className="px-3 py-2 font-medium">
                      {amount.label}
                      {unitOf(amount) && ` (${unitOf(amount)})`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {selected.map((plot) => (
                  <tr key={plot.id}>
                    <td className="px-3 py-2">
                      <p className="text-gray-900">{plot.name}</p>
                      <p className="text-xs text-gray-400">{fmtNumber(plot.area, 2, 'ha')}</p>
                    </td>
                    {amounts.map((amount) => (
                      <td key={amount.field} className="px-3 py-2">
                        <input
                          type="number"
                          inputMode="decimal"
                          step={amount.step}
                          min="0"
                          aria-label={`${amount.label} de ${plot.name}`}
                          value={rowValue(plot.id, amount.field)}
                          onChange={(e) => onRowChange(plot.id, amount.field, e.target.value)}
                          className={`${inputClass()} min-w-24 py-1.5`}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <SplitNote selected={selected} amounts={amounts} totals={totals} rowValue={rowValue} unitOf={unitOf} />
        </>
      )}
    </div>
  )
}

/** Cómo se repartió y si la suma de los lotes dejó de coincidir con el total */
function SplitNote({
  selected,
  amounts,
  totals,
  rowValue,
  unitOf,
}: {
  selected: Plot[]
  amounts: AmountInfo[]
  totals: Record<AmountField, string>
  rowValue: (plotId: number, field: AmountField) => string
  unitOf: (amount: AmountInfo) => string
}) {
  const mismatches = amounts.flatMap((amount) => {
    if (totals[amount.field].trim() === '') return []
    const sum = selected.reduce((acc, plot) => acc + (Number(rowValue(plot.id, amount.field)) || 0), 0)
    const total = Number(totals[amount.field])
    const tolerance = 10 ** -amount.decimals / 2
    return Math.abs(sum - total) > tolerance
      ? [`${amount.label}: los lotes suman ${fmtNumber(sum, amount.decimals, unitOf(amount))} y el total es ${fmtNumber(total, amount.decimals, unitOf(amount))}`]
      : []
  })

  return (
    <div className="flex flex-col gap-1 text-xs">
      <p className="text-gray-400">
        {splitsByArea(selected)
          ? 'Repartido según el área de cada lote; puedes ajustar cada uno.'
          : 'Repartido en partes iguales porque algún lote no tiene área; puedes ajustar cada uno.'}
      </p>
      {mismatches.map((message) => (
        <p key={message} className="text-amber-700">{message}. Se guarda lo de cada lote.</p>
      ))}
    </div>
  )
}
