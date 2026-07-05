import { useEffect, useState } from 'react'
import { CirclePlus, Search, ShoppingBag } from 'lucide-react'

import { runWithAlert } from '../../hooks/useSafeAction'
import { SaleColumns } from './models/columns'
import type { Sale, SaleDetail, RoastedCoffeeProduct, CreateSalePayload } from './models/types'
import {
  fetchSales,
  fetchSaleById,
  createSale,
  updateSale,
  deleteSale,
  fetchSaleCustomers,
  fetchSaleUsers,
  fetchRoastedCoffeeInventory,
} from './services/sales.api'

import DataTable from '../../components/ui/DataTable'
import SaleFormModal from './components/SaleFormModal'
import SaleDetailModal from './components/SaleDetailModal'

import { useAuth } from '../auth/AuthContext'
import type { Customer } from '../customers/models/types'
import type { User } from '../users/models/types'
import type { PaymentMethod } from '../expenses/models/types'
import { fetchPaymentMethods } from '../expenses/services/expenses.api'

export default function SalesPage() {
  const [data, setData] = useState<Sale[]>([])
  const [search, setSearch] = useState('')

  // ── Create / edit modal ────────────────────────────────────────────────────
  const [addingSale, setAddingSale] = useState(false)
  const [editingSale, setEditingSale] = useState<Sale | null>(null)
  const [editingDetails, setEditingDetails] = useState<SaleDetail[]>([])

  // ── Detail view modal ──────────────────────────────────────────────────────
  const [viewingSale, setViewingSale] = useState<Sale | null>(null)

  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  // ── Support data ───────────────────────────────────────────────────────────
  const [customers, setCustomers] = useState<Customer[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [products, setProducts] = useState<RoastedCoffeeProduct[]>([])
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])

  useEffect(() => {
    fetchSaleCustomers().then(setCustomers).catch(() => setCustomers([]))
    fetchSaleUsers().then(setUsers).catch(() => setUsers([]))
    fetchRoastedCoffeeInventory().then(setProducts).catch(() => setProducts([]))
    fetchPaymentMethods().then(setPaymentMethods).catch(() => setPaymentMethods([]))
  }, [])

  // ── Data loading ───────────────────────────────────────────────────────────

  const loadSales = async () => {
    try {
      const result = await fetchSales({ search })
      setData(result)
    } catch {
      setData([])
    }
  }

  useEffect(() => {
    loadSales()
  }, [search])

  // ── Open detail modal ──────────────────────────────────────────────────────

  const handleView = async (sale: Sale) => {
    try {
      const full = await fetchSaleById(sale.id)
      setViewingSale(full)
    } catch {
      setViewingSale(sale)
    }
  }

  // ── Create ─────────────────────────────────────────────────────────────────

  const handleCreate = async (payload: CreateSalePayload) => {
    await runWithAlert(async () => {
      await createSale(payload)
      await loadSales()
      setAddingSale(false)
    }, 'Venta creada correctamente')
  }

  // ── Edit ───────────────────────────────────────────────────────────────────

  const handleEdit = async (sale: Sale) => {
    const full = await fetchSaleById(sale.id)
    setEditingSale(full)
    setEditingDetails(full.details ?? [])
  }

  const handleUpdate = async (payload: CreateSalePayload) => {
    if (!editingSale) return
    await runWithAlert(async () => {
      await updateSale(editingSale.id, payload)
      await loadSales()
      setEditingSale(null)
      setEditingDetails([])
    }, 'Venta actualizada correctamente')
  }

  const handleDelete = async () => {
    if (!editingSale) return
    await runWithAlert(async () => {
      await deleteSale(editingSale.id)
      await loadSales()
      setEditingSale(null)
      setEditingDetails([])
    }, 'Venta eliminada correctamente')
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-6">
      {/* Page title */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-100 rounded-xl">
            <ShoppingBag className="w-6 h-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Ventas</h1>
            <p className="text-sm text-gray-400">{data.length} venta{data.length !== 1 ? 's' : ''} registrada{data.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
        {isAdmin && (
          <button onClick={() => setAddingSale(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
            <CirclePlus className="w-4 h-4" /> Nueva venta
          </button>
        )}
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar venta…"
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
        />
      </div>

      {/* Table */}
      <DataTable
        columns={SaleColumns}
        data={data}
        onEdit={isAdmin ? handleEdit : undefined}
        onView={handleView}
        isAdmin={isAdmin}
      />

      {/* Create modal */}
      {addingSale && (
        <SaleFormModal
          onClose={() => setAddingSale(false)}
          onSave={handleCreate}
          customers={customers}
          users={users}
          products={products}
          paymentMethods={paymentMethods}
          isAdmin={isAdmin}
        />
      )}

      {/* Edit modal */}
      {editingSale && (
        <SaleFormModal
          onClose={() => {
            setEditingSale(null)
            setEditingDetails([])
          }}
          onSave={handleUpdate}
          onDelete={handleDelete}
          customers={customers}
          users={users}
          products={products}
          paymentMethods={paymentMethods}
          initialSale={editingSale}
          initialDetails={editingDetails}
          isEdit
          isAdmin={isAdmin}
        />
      )}

      {/* Detail view modal */}
      {viewingSale && (
        <SaleDetailModal
          sale={viewingSale}
          onClose={() => setViewingSale(null)}
        />
      )}
    </div>
  )
}
