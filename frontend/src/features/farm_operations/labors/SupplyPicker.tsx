import { useCallback, useId, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { FlaskConical, Plus, Search } from 'lucide-react'
import { FieldShell } from '../components/fields'
import { inputClass } from '../components/styles'
import { useLoader } from '../components/useLoader'
import { SUPPLY_TYPE_LABELS } from '../models/labels'
import type { Supply, SupplyRef, SupplyType } from '../models/types'
import { fetchSupplies } from '../services/supplies.api'
import SupplyFormDialog from '../supplies/SupplyFormDialog'

const MAX_RESULTS = 6

interface SupplyPickerProps {
  label: string
  selected: SupplyRef | null
  onSelect: (supply: SupplyRef | null) => void
  error?: string
  /** Tipos que se listan primero; el primero es el tipo de un insumo nuevo */
  preferredTypes: SupplyType[]
}

/**
 * Elegir un insumo del catálogo buscando por nombre o composición, o
 * crearlo al vuelo sin salir del formulario de la labor.
 */
export default function SupplyPicker({ label, selected, onSelect, error, preferredTypes }: SupplyPickerProps) {
  const id = useId()
  const load = useCallback(() => fetchSupplies({ active: true }), [])
  const { data: supplies, reload } = useLoader(load)
  const [query, setQuery] = useState('')
  const [creating, setCreating] = useState(false)

  const results = useMemo(() => {
    const text = query.trim().toLowerCase()
    const rank = (supply: Supply) => (preferredTypes.includes(supply.supply_type) ? 0 : 1)
    return (supplies ?? [])
      .filter((supply) =>
        !text || supply.name.toLowerCase().includes(text) || (supply.composition ?? '').toLowerCase().includes(text),
      )
      .sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name))
  }, [supplies, query, preferredTypes])

  const exactMatch = results.some((supply) => supply.name.toLowerCase() === query.trim().toLowerCase())
  const choose = (supply: Supply) => {
    onSelect({ id: supply.id, name: supply.name, unit: supply.unit })
    setQuery('')
  }

  return (
    <FieldShell id={id} label={label} required error={error} wide>
      {selected ? (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2.5">
          <span className="flex items-center gap-2 text-sm text-emerald-900">
            <FlaskConical className="h-4 w-4" />
            <span className="font-medium">{selected.name}</span>
            <span className="text-emerald-700">· {selected.unit}</span>
          </span>
          <button
            type="button"
            onClick={() => onSelect(null)}
            className="text-xs font-medium text-emerald-800 hover:underline"
          >
            Cambiar
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              id={id}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar por nombre o composición…"
              autoComplete="off"
              className={`${inputClass(error)} pl-9`}
            />
          </div>
          <ul className="flex flex-col gap-1">
            {results.slice(0, MAX_RESULTS).map((supply) => (
              <li key={supply.id}>
                <button
                  type="button"
                  onClick={() => choose(supply)}
                  className="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-gray-50"
                >
                  <span className="text-gray-900">
                    {supply.name}
                    {supply.composition && <span className="text-gray-400"> · {supply.composition}</span>}
                  </span>
                  <span className="text-xs text-gray-400">
                    {SUPPLY_TYPE_LABELS[supply.supply_type]} · {supply.unit}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {supplies && results.length > MAX_RESULTS && (
            <p className="px-3 text-xs text-gray-400">Escribe para ver más insumos.</p>
          )}
          {supplies && !exactMatch && (
            <button
              type="button"
              onClick={() => setCreating(true)}
              className="flex w-fit items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-emerald-800 hover:bg-emerald-50"
            >
              <Plus className="h-4 w-4" />
              {query.trim() ? `Crear «${query.trim()}»` : 'Nuevo insumo'}
            </button>
          )}
        </div>
      )}

      {/* Fuera del formulario de la labor: un formulario no puede ir dentro de otro */}
      {creating &&
        createPortal(
          <SupplyFormDialog
            defaultType={preferredTypes[0]}
            initialName={query.trim()}
            onClose={() => setCreating(false)}
            onSaved={(supply) => {
              setCreating(false)
              reload()
              choose(supply)
            }}
          />,
          document.body,
        )}
    </FieldShell>
  )
}
