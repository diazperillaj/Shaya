import { useCallback, useState } from 'react'
import { CirclePlus, FlaskConical, Pencil, Search, Trash2 } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import { Badge, Button, EmptyState, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { plural } from '../format'
import { SUPPLY_TYPE_LABELS } from '../models/labels'
import type { Supply, SupplyType } from '../models/types'
import { deleteSupply, fetchSupplies, setSupplyActive } from '../services/supplies.api'
import SupplyFormDialog from './SupplyFormDialog'

const TYPE_FILTERS: { value: SupplyType | ''; label: string }[] = [
  { value: '', label: 'Todos' },
  ...(Object.entries(SUPPLY_TYPE_LABELS) as [SupplyType, string][]).map(([value, label]) => ({ value, label })),
]

/**
 * Catálogo de insumos agrícolas, compartido por todas las fincas.
 *
 * Cualquiera del módulo agrega y corrige insumos; desactivar y eliminar
 * queda para el administrador (los registros históricos los referencian).
 */
export default function SuppliesPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [type, setType] = useState<SupplyType | ''>('')
  const [search, setSearch] = useState('')
  const [showInactive, setShowInactive] = useState(false)
  const [dialog, setDialog] = useState<{ supply?: Supply } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const load = useCallback(
    () => fetchSupplies({ supply_type: type || undefined, search, active: showInactive ? undefined : true }),
    [type, search, showInactive],
  )
  const { data: supplies, error, loading, reload } = useLoader(load)

  const runAction = async (action: () => Promise<unknown>) => {
    setActionError(null)
    try {
      await action()
      reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Error actualizando el insumo')
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={FlaskConical}
        title="Insumos"
        subtitle="Catálogo compartido de fertilizantes, fitosanitarios y demás insumos de las labores."
        actions={
          <Button variant="primary" icon={CirclePlus} onClick={() => setDialog({})}>
            Nuevo insumo
          </Button>
        }
      />

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          {TYPE_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              onClick={() => setType(filter.value)}
              className={`rounded-full px-3.5 py-1.5 text-sm transition ${
                type === filter.value
                  ? 'bg-emerald-900 text-white'
                  : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative w-full max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nombre o composición…"
              className="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/25"
            />
          </div>
          {isAdmin && (
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="h-4 w-4 accent-emerald-800"
              />
              Ver también los desactivados
            </label>
          )}
        </div>
      </div>

      {(error || actionError) && <ErrorMessage message={(error ?? actionError) as string} />}
      {loading && <Loading />}

      {supplies && supplies.length === 0 && (
        <EmptyState
          icon={FlaskConical}
          title="No hay insumos con estos filtros"
          description="Los insumos se agregan aquí o directamente desde el formulario de cada labor."
        />
      )}

      {supplies && supplies.length > 0 && (
        <div className="rounded-2xl border border-gray-100 bg-white shadow-sm">
          <p className="border-b border-gray-100 px-5 py-3 text-xs text-gray-400">
            {plural(supplies.length, 'insumo', 'insumos')}
          </p>
          <ul className="divide-y divide-gray-100">
            {supplies.map((supply) => (
              <li key={supply.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3">
                <div className={supply.active ? '' : 'opacity-60'}>
                  <p className="flex flex-wrap items-center gap-2 text-sm font-medium text-gray-900">
                    {supply.name}
                    <Badge tone="green">
                      {supply.supply_type === 'other' ? supply.other_detail : SUPPLY_TYPE_LABELS[supply.supply_type]}
                    </Badge>
                    {!supply.active && <Badge>Desactivado</Badge>}
                  </p>
                  <p className="text-xs text-gray-400">
                    Unidad: {supply.unit}
                    {supply.composition && ` · ${supply.composition}`}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() => runAction(() => setSupplyActive(supply.id, !supply.active))}
                      className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100"
                    >
                      {supply.active ? 'Desactivar' : 'Activar'}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setDialog({ supply })}
                    aria-label={`Editar ${supply.name}`}
                    className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 hover:text-emerald-800"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm(`¿Eliminar «${supply.name}» del catálogo? Si ya se usó en labores, desactívalo en su lugar.`)) {
                          runAction(() => deleteSupply(supply.id))
                        }
                      }}
                      aria-label={`Eliminar ${supply.name}`}
                      className="rounded-lg p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {dialog && (
        <SupplyFormDialog
          supply={dialog.supply}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            reload()
          }}
        />
      )}
    </div>
  )
}
