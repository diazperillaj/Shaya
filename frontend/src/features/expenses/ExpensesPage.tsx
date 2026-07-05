import { useEffect, useState } from 'react'
import { CirclePlus, Search, Receipt, Tags, Wallet, X } from 'lucide-react'

import { runWithAlert } from '../../hooks/useSafeAction'
import DataTable from '../../components/ui/DataTable'
import { useAuth } from '../auth/AuthContext'

import { ExpenseColumns } from './models/columns'
import type {
  ExpenseCategory,
  GeneralExpense,
  PaymentMethod,
  UpdateExpensePayload,
} from './models/types'
import {
  createExpense,
  createExpenseCategory,
  createPaymentMethod,
  deleteExpense,
  deleteExpenseCategory,
  deletePaymentMethod,
  fetchExpenseCategories,
  fetchExpenses,
  fetchPaymentMethods,
  updateExpense,
  updateExpenseCategory,
  updatePaymentMethod,
} from './services/expenses.api'

import ExpenseFormModal from './components/ExpenseFormModal'
import CatalogModal from './components/CatalogModal'

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function ExpensesPage() {
  const [data, setData] = useState<GeneralExpense[]>([])
  const [categories, setCategories] = useState<ExpenseCategory[]>([])
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])

  // ── Filters ────────────────────────────────────────────────────────────────
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  // ── Modals ─────────────────────────────────────────────────────────────────
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState<GeneralExpense | null>(null)
  const [managingCategories, setManagingCategories] = useState(false)
  const [managingMethods, setManagingMethods] = useState(false)

  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  // ── Data loading ───────────────────────────────────────────────────────────

  const loadCatalogs = async () => {
    fetchExpenseCategories().then(setCategories).catch(() => setCategories([]))
    fetchPaymentMethods().then(setPaymentMethods).catch(() => setPaymentMethods([]))
  }

  const loadExpenses = async () => {
    try {
      const result = await fetchExpenses({
        search: search || undefined,
        category_id: categoryId ? parseInt(categoryId) : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      })
      setData(result)
    } catch {
      setData([])
    }
  }

  useEffect(() => { loadCatalogs() }, [])
  useEffect(() => { loadExpenses() }, [search, categoryId, dateFrom, dateTo])

  const totalFiltered = data.reduce((sum, e) => sum + e.amount, 0)

  // ── CRUD handlers ──────────────────────────────────────────────────────────

  const handleCreate = async (payload: UpdateExpensePayload) => {
    await runWithAlert(async () => {
      await createExpense(payload)
      await loadExpenses()
      setAdding(false)
    }, 'Gasto creado correctamente')
  }

  const handleUpdate = async (payload: UpdateExpensePayload) => {
    if (!editing) return
    await runWithAlert(async () => {
      await updateExpense(editing.id, payload)
      await loadExpenses()
      setEditing(null)
    }, 'Gasto actualizado correctamente')
  }

  const handleDelete = async () => {
    if (!editing) return
    await runWithAlert(async () => {
      await deleteExpense(editing.id)
      await loadExpenses()
      setEditing(null)
    }, 'Gasto eliminado correctamente')
  }

  const clearFilters = () => {
    setSearch('')
    setCategoryId('')
    setDateFrom('')
    setDateTo('')
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-6">
      {/* Page title */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-100 rounded-xl">
            <Receipt className="w-6 h-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Gastos</h1>
            <p className="text-sm text-gray-400">
              {data.length} gasto{data.length !== 1 ? 's' : ''} · Total: {fmtCOP(totalFiltered)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setManagingCategories(true)}
            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2.5 rounded-xl text-sm font-medium shadow-sm transition-all"
          >
            <Tags className="w-4 h-4" /> Categorías
          </button>
          <button
            onClick={() => setManagingMethods(true)}
            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2.5 rounded-xl text-sm font-medium shadow-sm transition-all"
          >
            <Wallet className="w-4 h-4" /> Métodos de pago
          </button>
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all"
          >
            <CirclePlus className="w-4 h-4" /> Nuevo gasto
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-lg p-5 border border-gray-100">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[180px]">
            <label className="flex text-sm font-semibold text-gray-700 mb-2">Buscar motivo</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar…"
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
              />
            </div>
          </div>

          <div className="min-w-[160px]">
            <label className="flex text-sm font-semibold text-gray-700 mb-2">Categoría</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
            >
              <option value="">Todas</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="flex text-sm font-semibold text-gray-700 mb-2">Desde</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
            />
          </div>

          <div>
            <label className="flex text-sm font-semibold text-gray-700 mb-2">Hasta</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
            />
          </div>

          <button
            onClick={clearFilters}
            className="h-11 flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-5 rounded-xl text-sm font-medium border border-gray-200 transition-all"
          >
            <X className="w-4 h-4" /> Limpiar
          </button>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={ExpenseColumns}
        data={data}
        onEdit={isAdmin ? setEditing : undefined}
        isAdmin={isAdmin}
        emptyMessage="Sin gastos registrados"
      />

      {/* Create / edit expense */}
      {adding && (
        <ExpenseFormModal
          onClose={() => setAdding(false)}
          onSave={handleCreate}
          categories={categories}
          paymentMethods={paymentMethods}
        />
      )}
      {editing && (
        <ExpenseFormModal
          onClose={() => setEditing(null)}
          onSave={handleUpdate}
          onDelete={isAdmin ? handleDelete : undefined}
          categories={categories}
          paymentMethods={paymentMethods}
          initial={editing}
          isEdit
        />
      )}

      {/* Catalog managers */}
      {managingCategories && (
        <CatalogModal
          title="Categorías de gastos"
          items={categories}
          isAdmin={isAdmin}
          onClose={() => setManagingCategories(false)}
          onCreate={async (name) => { await createExpenseCategory(name); await loadCatalogs() }}
          onUpdate={async (id, name) => { await updateExpenseCategory(id, name); await loadCatalogs(); await loadExpenses() }}
          onDelete={async (id) => { await deleteExpenseCategory(id); await loadCatalogs() }}
        />
      )}
      {managingMethods && (
        <CatalogModal
          title="Métodos de pago"
          items={paymentMethods}
          isAdmin={isAdmin}
          onClose={() => setManagingMethods(false)}
          onCreate={async (name) => { await createPaymentMethod(name); await loadCatalogs() }}
          onUpdate={async (id, name) => { await updatePaymentMethod(id, name); await loadCatalogs(); await loadExpenses() }}
          onDelete={async (id) => { await deletePaymentMethod(id); await loadCatalogs() }}
        />
      )}
    </div>
  )
}
