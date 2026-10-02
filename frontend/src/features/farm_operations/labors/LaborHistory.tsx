import { useState } from 'react'
import { fmtDate, fmtMoney } from '../format'
import type { AnyLabor, LaborKind } from '../models/types'
import { LABOR_INFO, LABOR_KINDS, describeLabor, laborDate } from './laborConfig'

/**
 * Labores de un ciclo: un resumen por tipo que sirve de filtro y la lista
 * de registros, del más reciente al más antiguo. Tocar un registro lo abre
 * para corregirlo.
 */
export default function LaborHistory({ labors, onEdit }: { labors: AnyLabor[]; onEdit: (labor: AnyLabor) => void }) {
  const [filter, setFilter] = useState<LaborKind | null>(null)
  const visible = filter ? labors.filter((labor) => labor.kind === filter) : labors

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {LABOR_KINDS.map((kind) => {
          const { icon: Icon, plural } = LABOR_INFO[kind]
          const ofKind = labors.filter((labor) => labor.kind === kind)
          const cost = ofKind.reduce((sum, labor) => sum + (('cost' in labor.record && labor.record.cost) || 0), 0)
          const active = filter === kind
          return (
            <button
              key={kind}
              type="button"
              onClick={() => setFilter(active ? null : kind)}
              aria-pressed={active}
              className={`flex flex-col items-start gap-1 rounded-xl border px-3 py-2.5 text-left transition ${
                active ? 'border-emerald-300 bg-emerald-50' : 'border-gray-100 hover:bg-gray-50'
              }`}
            >
              <span className="flex items-center gap-1.5 text-xs text-gray-500">
                <Icon className="h-3.5 w-3.5" /> {plural}
              </span>
              <span className="text-lg font-semibold text-gray-900">{ofKind.length}</span>
              <span className="text-xs text-gray-400">
                {ofKind.length > 0 ? `Última: ${fmtDate(laborDate(ofKind[0]))}` : 'Sin registros'}
                {cost > 0 && <> · {fmtMoney(cost)}</>}
              </span>
            </button>
          )
        })}
      </div>

      {visible.length === 0 ? (
        <p className="text-sm text-gray-400">
          {filter ? `Sin ${LABOR_INFO[filter].plural.toLowerCase()} en este ciclo.` : 'Sin labores en este ciclo. Registra la primera con «Registrar labor».'}
        </p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {visible.map((labor) => {
            const Icon = LABOR_INFO[labor.kind].icon
            const { title, detail } = describeLabor(labor)
            return (
              <li key={`${labor.kind}-${labor.record.id}`}>
                <button
                  type="button"
                  onClick={() => onEdit(labor)}
                  className="-mx-2 flex w-[calc(100%+1rem)] items-start gap-3 rounded-xl px-2 py-2.5 text-left hover:bg-gray-50"
                >
                  <Icon className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-700" />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium text-gray-900">{title}</span>
                    <span className="block text-xs text-gray-500">{detail}</span>
                    {labor.record.observations && (
                      <span className="block truncate text-xs text-gray-400">{labor.record.observations}</span>
                    )}
                  </span>
                  <span className="whitespace-nowrap text-xs text-gray-400">{fmtDate(laborDate(labor))}</span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
