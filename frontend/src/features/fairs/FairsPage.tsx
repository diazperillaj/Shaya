import { useEffect, useState, useMemo } from 'react'
import { CirclePlus, CupSoda, Search, Store } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import CatalogModal from '../expenses/components/CatalogModal'
import FairDetailPage from './FairDetailPage'
import FairReportPage from './FairReportPage'
import { makeFairColumns } from './models/columns'
import {
  fetchFairs, createFair, updateFair, deleteFair,
  fetchFairById, fetchRoastedCoffeeForFair,
  fetchFairProducts, createFairProduct, updateFairProduct, deleteFairProduct,
} from './services/fairs.api'
import type { Fair, FairProduct } from './models/types'
import type { RoastedCoffeeProduct } from '../sales/models/types'

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

type View = 'list' | 'detail' | 'report'

const fairFields = [
  { accessor: 'name' as const, header: 'Nombre', type: 'text' as const },
  { accessor: 'location' as const, header: 'Ubicación', type: 'text' as const },
  { accessor: 'start_datetime' as const, header: 'Fecha y hora de inicio', type: 'datetime-local' as const },
  { accessor: 'observations' as const, header: 'Observaciones', type: 'textarea' as const },
]

type FairFormShape = { name: string; location: string; start_datetime: string; observations: string }

const emptyForm: FairFormShape = { name: '', location: '', start_datetime: '', observations: '' }

export default function FairsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [view, setView] = useState<View>('list')
  const [fairs, setFairs] = useState<Fair[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  // Detail / report navigation
  const [selectedFair, setSelectedFair] = useState<Fair | null>(null)

  // Modals
  const [addingFair, setAddingFair] = useState(false)
  const [editingFair, setEditingFair] = useState<Fair | null>(null)
  const [managingProducts, setManagingProducts] = useState(false)

  // Support data
  const [products, setProducts] = useState<RoastedCoffeeProduct[]>([])
  const [fairProducts, setFairProducts] = useState<FairProduct[]>([])

  // ── Load data ────────────────────────────────────────────────────────────────

  const loadFairs = async () => {
    setLoading(true)
    try { setFairs(await fetchFairs(search || undefined)) }
    catch { setFairs([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadFairs() }, [search])

  useEffect(() => {
    fetchRoastedCoffeeForFair().then(setProducts).catch(() => setProducts([]))
    loadFairProducts()
  }, [])

  const loadFairProducts = async () => {
    try { setFairProducts(await fetchFairProducts()) }
    catch { setFairProducts([]) }
  }

  // ── Handlers ─────────────────────────────────────────────────────────────────

  const handleCreate = async (data: FairFormShape) => {
    try {
      const created = await createFair({
        name: data.name,
        location: data.location || undefined,
        start_datetime: data.start_datetime,
        observations: data.observations || undefined,
      })
      setFairs(prev => [created, ...prev])
      setAddingFair(false)
    } catch (e: any) { alert(e.message) }
  }

  const handleUpdate = async (data: FairFormShape) => {
    if (!editingFair) return
    try {
      const updated = await updateFair(editingFair.id, {
        name: data.name,
        location: data.location || undefined,
        start_datetime: data.start_datetime,
        observations: data.observations || undefined,
      })
      setFairs(prev => prev.map(f => f.id === updated.id ? updated : f))
      setEditingFair(null)
    } catch (e: any) { alert(e.message) }
  }

  const handleDelete = async () => {
    if (!editingFair) return
    const confirmMsg = editingFair.status === 'closed'
      ? '¿Eliminar esta feria cerrada?\n\nSe devolverán al inventario las unidades vendidas y se eliminará la venta consolidada generada al cierre. Esta acción no se puede deshacer.'
      : '¿Eliminar esta feria?\n\nTodo el inventario asignado volverá al stock general y se eliminarán sus ventas y gastos. Esta acción no se puede deshacer.'
    if (!confirm(confirmMsg)) return
    try {
      await deleteFair(editingFair.id)
      setFairs(prev => prev.filter(f => f.id !== editingFair.id))
      setEditingFair(null)
    } catch (e: any) { alert(e.message) }
  }

  const handleOpenDetail = async (fair: Fair) => {
    try {
      const full = await fetchFairById(fair.id)
      setSelectedFair(full)
      setView('detail')
    } catch { setSelectedFair(fair); setView('detail') }
  }

  const handleOpenReport = (fair: Fair) => {
    setSelectedFair(fair)
    setView('report')
  }

  const handleFairUpdated = (updated: Fair) => {
    setSelectedFair(updated)
    setFairs(prev => prev.map(f => f.id === updated.id ? updated : f))
  }

  const handleBack = () => {
    setView('list')
    setSelectedFair(null)
  }

  // ── Columns ──────────────────────────────────────────────────────────────────

  const columns = useMemo(
    () => makeFairColumns(handleOpenDetail, handleOpenReport, fair => setEditingFair(fair)),
    [],
  )

  // ── Edit modal initial value ─────────────────────────────────────────────────

  const editInitial: FairFormShape | null = editingFair
    ? {
        name: editingFair.name,
        location: editingFair.location ?? '',
        start_datetime: editingFair.startDatetime.slice(0, 16),
        observations: editingFair.observations ?? '',
      }
    : null

  // ── Views ─────────────────────────────────────────────────────────────────────

  if (view === 'detail' && selectedFair) {
    return (
      <FairDetailPage
        fair={selectedFair}
        products={products}
        fairProducts={fairProducts}
        isAdmin={isAdmin}
        onBack={handleBack}
        onFairUpdated={handleFairUpdated}
      />
    )
  }

  if (view === 'report' && selectedFair) {
    return (
      <FairReportPage
        fairId={selectedFair.id}
        fairName={selectedFair.name}
        onBack={handleBack}
      />
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-100 rounded-xl">
            <Store className="w-6 h-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ferias</h1>
            <p className="text-sm text-gray-400">{fairs.length} feria{fairs.length !== 1 ? 's' : ''} registrada{fairs.length !== 1 ? 's' : ''}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setManagingProducts(true)}
            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-5 py-2.5 rounded-xl text-sm font-medium shadow-sm transition-all"
          >
            <CupSoda className="w-4 h-4" /> Productos de feria
          </button>
          {isAdmin && (
            <button
              onClick={() => setAddingFair(true)}
              className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all"
            >
              <CirclePlus className="w-4 h-4" /> Nueva feria
            </button>
          )}
        </div>
      </div>

      {/* Search bar */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Buscar feria…"
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-12 text-gray-400">Cargando ferias…</div>
      ) : (
        <DataTable
          data={fairs}
          columns={columns}
          isAdmin={isAdmin}
        />
      )}

      {/* Create modal */}
      {addingFair && (
        <Modal
          item={emptyForm}
          fields={fairFields}
          onClose={() => setAddingFair(false)}
          onSave={handleCreate as any}
          mode="add"
          title="feria"
        />
      )}

      {/* Fair products catalog */}
      {managingProducts && (
        <CatalogModal
          title="Productos de feria"
          items={fairProducts.map(p => ({ id: p.id, name: p.name, value: p.defaultPrice }))}
          isAdmin={isAdmin}
          valueLabel="Precio"
          formatValue={fmtCOP}
          onClose={() => setManagingProducts(false)}
          onCreate={async (name, value) => { await createFairProduct({ name, default_price: value! }); await loadFairProducts() }}
          onUpdate={async (id, name, value) => { await updateFairProduct(id, { name, default_price: value! }); await loadFairProducts() }}
          onDelete={async (id) => { await deleteFairProduct(id); await loadFairProducts() }}
        />
      )}

      {/* Edit modal */}
      {editingFair && editInitial && (
        <Modal
          item={editInitial}
          fields={fairFields}
          onClose={() => setEditingFair(null)}
          onSave={handleUpdate as any}
          onDelete={handleDelete as any}
          mode="edit"
          title="feria"
        />
      )}
    </div>
  )
}
