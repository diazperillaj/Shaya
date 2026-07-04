import { useEffect, useState } from 'react'
import { CirclePlus, Search, ArrowRightLeft } from 'lucide-react'

import DataTable from '../../components/ui/DataTable'
import { movementColumns } from './models/columns'
import type { RoastedMovement } from './models/types'
import { fetchMovements, createMovement, deleteMovement } from './services/movements.api'
import MovementFormModal from './components/MovementFormModal'
import type { RoastedMovementCreate } from './models/types'
import { useAuth } from '../auth/AuthContext'
import { runWithAlert } from '../../hooks/useSafeAction'

export default function MovementsPage() {
  const [data, setData] = useState<RoastedMovement[]>([])
  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState(false)
  const { user } = useAuth()

  const load = async () => {
    try {
      setData(await fetchMovements())
    } catch {
      setData([])
    }
  }

  useEffect(() => { load() }, [])

  const filtered = data.filter((m) => {
    const s = search.toLowerCase()
    return (
      String(m.id).includes(s) ||
      (m.observations ?? '').toLowerCase().includes(s) ||
      m.details.some((d) => d.product_name.toLowerCase().includes(s))
    )
  })

  const handleCreate = async (payload: RoastedMovementCreate) => {
    await runWithAlert(async () => {
      await createMovement(payload)
      await load()
      setAdding(false)
    }, 'Movimiento registrado correctamente')
  }

  const handleDelete = async (item: RoastedMovement) => {
    const ok = window.confirm(`¿Eliminar el movimiento #${item.id}? El stock será restaurado.`)
    if (!ok) return
    await runWithAlert(async () => {
      await deleteMovement(item.id)
      await load()
    }, 'Movimiento eliminado y stock restaurado')
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-100 rounded-xl">
            <ArrowRightLeft className="w-6 h-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Movimientos</h1>
            <p className="text-sm text-gray-400">
              {data.length} movimiento{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        {user?.role === 'admin' && (
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all"
          >
            <CirclePlus className="w-4 h-4" /> Nuevo movimiento
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar movimiento…"
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
        />
      </div>

      {/* Table */}
      <DataTable
        columns={movementColumns}
        data={filtered}
        onDelete={handleDelete}
        isAdmin={user?.role === 'admin'}
      />

      {adding && (
        <MovementFormModal
          onClose={() => setAdding(false)}
          onSave={handleCreate}
        />
      )}
    </div>
  )
}
