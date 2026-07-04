import { useState } from 'react'
import { ArrowLeft, CirclePlus, Lock, Package, ShoppingBag, Receipt, Pencil } from 'lucide-react'
import Modal from '../../components/ui/Modal'
import FairSaleModal from './components/FairSaleModal'
import {
  createFairInventory, updateFairInventory, deleteFairInventory,
  createFairSale, updateFairSale, deleteFairSale,
  createFairExpense, updateFairExpense, deleteFairExpense,
  closeFair,
} from './services/fairs.api'
import type { Fair, FairInventory, FairSale, FairExpense } from './models/types'
import type { RoastedCoffeeProduct } from '../sales/models/types'

interface Props {
  fair: Fair
  products: RoastedCoffeeProduct[]
  isAdmin: boolean
  onBack: () => void
  onFairUpdated: (fair: Fair) => void
}

type Tab = 'inventory' | 'sales' | 'expenses'

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const fmtDT = (iso: string) =>
  new Date(iso).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })

const EXPENSE_OPTIONS = [
  { value: 'food', label: 'Alimentación' },
  { value: 'supplies', label: 'Insumos' },
  { value: 'transport', label: 'Transporte' },
  { value: 'other', label: 'Otros' },
]

export default function FairDetailPage({ fair, products, isAdmin, onBack, onFairUpdated }: Props) {
  const [tab, setTab] = useState<Tab>('sales')
  const [addingInv, setAddingInv] = useState(false)
  const [editingInv, setEditingInv] = useState<FairInventory | null>(null)
  const [addingSale, setAddingSale] = useState(false)
  const [editingSale, setEditingSale] = useState<FairSale | null>(null)
  const [addingExp, setAddingExp] = useState(false)
  const [editingExp, setEditingExp] = useState<FairExpense | null>(null)
  const [closing, setClosing] = useState(false)

  const isOpen = fair.status === 'open'

  const refresh = (updated: Fair) => onFairUpdated(updated)

  // ── Close fair ─────────────────────────────────────────────────────────────

  const handleClose = async () => {
    if (!confirm('¿Cerrar la feria? Se generará la venta consolidada y se devolverá el inventario remanente.')) return
    setClosing(true)
    try { refresh(await closeFair(fair.id)) }
    catch (e: any) { alert(e.message) }
    finally { setClosing(false) }
  }

  // ── Inventory handlers ─────────────────────────────────────────────────────

  const handleAddInv = async (data: any) => {
    const updated = await createFairInventory(fair.id, {
      detail_roasted_coffee_id: Number(data.detail_roasted_coffee_id),
      initial_quantity: Number(data.initial_quantity),
      unit_value: Number(data.unit_value),
    })
    refresh(updated); setAddingInv(false)
  }

  const handleUpdateInv = async (data: any) => {
    if (!editingInv) return
    const updated = await updateFairInventory(fair.id, editingInv.id, {
      initial_quantity: Number(data.initial_quantity),
      unit_value: Number(data.unit_value),
    })
    refresh(updated); setEditingInv(null)
  }

  const handleDeleteInv = async () => {
    if (!editingInv || !confirm('¿Eliminar este ítem? El inventario se devolverá al stock general.')) return
    const updated = await deleteFairInventory(fair.id, editingInv.id)
    refresh(updated); setEditingInv(null)
  }

  // ── Sale handlers ──────────────────────────────────────────────────────────

  const handleAddSale = async (payload: any) => {
    refresh(await createFairSale(fair.id, payload))
  }

  const handleUpdateSale = async (payload: any) => {
    if (!editingSale) return
    refresh(await updateFairSale(fair.id, editingSale.id, payload))
  }

  const handleDeleteSale = async () => {
    if (!editingSale) return
    refresh(await deleteFairSale(fair.id, editingSale.id))
    setEditingSale(null)
  }

  // ── Expense handlers ───────────────────────────────────────────────────────

  const handleAddExp = async (data: any) => {
    const updated = await createFairExpense(fair.id, {
      category: data.category,
      description: data.description,
      amount: Number(data.amount),
    })
    refresh(updated); setAddingExp(false)
  }

  const handleUpdateExp = async (data: any) => {
    if (!editingExp) return
    const updated = await updateFairExpense(fair.id, editingExp.id, {
      category: data.category,
      description: data.description,
      amount: Number(data.amount),
    })
    refresh(updated); setEditingExp(null)
  }

  const handleDeleteExp = async () => {
    if (!editingExp || !confirm('¿Eliminar este gasto?')) return
    const updated = await deleteFairExpense(fair.id, editingExp.id)
    refresh(updated); setEditingExp(null)
  }

  // ── Inventory fields for Modal ─────────────────────────────────────────────

  const invProductOptions = products.map(p => ({
    value: p.detail_id,
    label: `${p.name} (${p.remaining_quantity} disp.)`,
  }))

  const addInvFields = [
    { accessor: 'detail_roasted_coffee_id' as const, header: 'Producto / Lote', type: 'select' as const, options: invProductOptions },
    { accessor: 'initial_quantity' as const, header: 'Cantidad (bolsas)', type: 'number' as const },
    { accessor: 'unit_value' as const, header: 'Precio de referencia por bolsa', type: 'number' as const },
  ]

  const editInvFields = [
    { accessor: 'initial_quantity' as const, header: 'Cantidad (bolsas)', type: 'number' as const },
    { accessor: 'unit_value' as const, header: 'Precio de referencia por bolsa', type: 'number' as const },
  ]

  const expFields = [
    { accessor: 'category' as const, header: 'Categoría', type: 'select' as const, options: EXPENSE_OPTIONS },
    { accessor: 'description' as const, header: 'Descripción', type: 'text' as const },
    { accessor: 'amount' as const, header: 'Monto ($)', type: 'number' as const },
  ]

  // ── Tabs ───────────────────────────────────────────────────────────────────

  const tabs: { id: Tab; label: string; icon: React.ReactNode; count: number }[] = [
    { id: 'sales', label: 'Ventas', icon: <ShoppingBag className="w-4 h-4" />, count: fair.fairSales.length },
    { id: 'expenses', label: 'Gastos', icon: <Receipt className="w-4 h-4" />, count: fair.expenses.length },
    { id: 'inventory', label: 'Inventario', icon: <Package className="w-4 h-4" />, count: fair.inventory.length },
  ]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-gray-900">{fair.name}</h1>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${isOpen ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                {isOpen ? 'Abierta' : 'Cerrada'}
              </span>
            </div>
            <p className="text-sm text-gray-400">{fair.location ?? '—'} · Desde {fmtDT(fair.startDatetime)}</p>
          </div>
        </div>

        {isOpen && isAdmin && (
          <button onClick={handleClose} disabled={closing}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-900 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50">
            <Lock className="w-4 h-4" /> {closing ? 'Cerrando…' : 'Cerrar feria'}
          </button>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4">
          <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">Total ventas</p>
          <p className="text-xl font-bold text-emerald-900 mt-1">{fmtCOP(fair.totalSales)}</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4">
          <p className="text-xs font-semibold text-red-600 uppercase tracking-wide">Total gastos</p>
          <p className="text-xl font-bold text-red-800 mt-1">{fmtCOP(fair.totalExpenses)}</p>
        </div>
        <div className={`border rounded-2xl p-4 ${fair.netProfit >= 0 ? 'bg-sky-50 border-sky-200' : 'bg-orange-50 border-orange-200'}`}>
          <p className={`text-xs font-semibold uppercase tracking-wide ${fair.netProfit >= 0 ? 'text-sky-600' : 'text-orange-600'}`}>Ganancia neta</p>
          <p className={`text-xl font-bold mt-1 ${fair.netProfit >= 0 ? 'text-sky-900' : 'text-orange-800'}`}>{fmtCOP(fair.netProfit)}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="flex border-b border-gray-100">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-4 text-sm font-medium transition-colors ${tab === t.id ? 'text-emerald-800 border-b-2 border-emerald-700 bg-emerald-50/50' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}>
              {t.icon} {t.label}
              <span className={`text-xs px-1.5 py-0.5 rounded-full font-semibold ${tab === t.id ? 'bg-emerald-700 text-white' : 'bg-gray-100 text-gray-500'}`}>{t.count}</span>
            </button>
          ))}
        </div>

        <div className="p-5">

          {/* ── Sales tab ── */}
          {tab === 'sales' && (
            <div className="flex flex-col gap-4">
              {isOpen && (
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">{fair.fairSales.length} venta{fair.fairSales.length !== 1 ? 's' : ''} registrada{fair.fairSales.length !== 1 ? 's' : ''}</p>
                  <button onClick={() => setAddingSale(true)}
                    className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all">
                    <CirclePlus className="w-4 h-4" /> Registrar venta
                  </button>
                </div>
              )}
              {fair.fairSales.length === 0 ? (
                <p className="text-center text-gray-400 text-sm py-8">No hay ventas registradas</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        {['#', 'Producto', 'Fecha', 'Cantidad', 'Precio unit.', 'Total', ''].map(h => (
                          <th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pb-2 pr-4">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {fair.fairSales.map(s => (
                        <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                          <td className="py-2.5 pr-4 text-gray-400 text-xs">{s.id}</td>
                          <td className="py-2.5 pr-4 font-medium text-gray-800">{s.productName}</td>
                          <td className="py-2.5 pr-4 text-gray-500">{fmtDT(s.saleDatetime)}</td>
                          <td className="py-2.5 pr-4 text-center font-semibold">{s.quantity}</td>
                          <td className="py-2.5 pr-4 text-gray-600">{fmtCOP(s.unitValue)}</td>
                          <td className="py-2.5 pr-4 font-bold text-emerald-800">{fmtCOP(s.total)}</td>
                          <td className="py-2.5 pr-4">
                            {isOpen && isAdmin && (
                              <div className="flex gap-1">
                                <button onClick={() => setEditingSale(s)} className="p-1.5 rounded-lg hover:bg-gray-100"><Pencil className="w-3.5 h-3.5 text-gray-500" /></button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 border-gray-200">
                        <td colSpan={5} className="pt-2.5 pr-4 text-sm font-semibold text-gray-700">Total</td>
                        <td className="pt-2.5 pr-4 font-bold text-emerald-900 text-base">{fmtCOP(fair.totalSales)}</td>
                        <td />
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── Expenses tab ── */}
          {tab === 'expenses' && (
            <div className="flex flex-col gap-4">
              {isOpen && (
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">{fair.expenses.length} gasto{fair.expenses.length !== 1 ? 's' : ''} registrado{fair.expenses.length !== 1 ? 's' : ''}</p>
                  <button onClick={() => setAddingExp(true)}
                    className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all">
                    <CirclePlus className="w-4 h-4" /> Registrar gasto
                  </button>
                </div>
              )}
              {fair.expenses.length === 0 ? (
                <p className="text-center text-gray-400 text-sm py-8">No hay gastos registrados</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        {['#', 'Categoría', 'Descripción', 'Fecha', 'Monto', ''].map(h => (
                          <th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pb-2 pr-4">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {fair.expenses.map(e => (
                        <tr key={e.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                          <td className="py-2.5 pr-4 text-gray-400 text-xs">{e.id}</td>
                          <td className="py-2.5 pr-4">
                            <span className="bg-gray-100 text-gray-700 text-xs px-2 py-0.5 rounded-full font-medium">{e.categoryLabel}</span>
                          </td>
                          <td className="py-2.5 pr-4 text-gray-700">{e.description}</td>
                          <td className="py-2.5 pr-4 text-gray-500">{fmtDT(e.expenseDatetime)}</td>
                          <td className="py-2.5 pr-4 font-bold text-red-700">{fmtCOP(e.amount)}</td>
                          <td className="py-2.5 pr-4">
                            {isOpen && isAdmin && (
                              <button onClick={() => setEditingExp(e)} className="p-1.5 rounded-lg hover:bg-gray-100"><Pencil className="w-3.5 h-3.5 text-gray-500" /></button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="border-t-2 border-gray-200">
                        <td colSpan={4} className="pt-2.5 pr-4 text-sm font-semibold text-gray-700">Total gastos</td>
                        <td className="pt-2.5 pr-4 font-bold text-red-800 text-base">{fmtCOP(fair.totalExpenses)}</td>
                        <td />
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* ── Inventory tab ── */}
          {tab === 'inventory' && (
            <div className="flex flex-col gap-4">
              {isOpen && (
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">{fair.inventory.length} lote{fair.inventory.length !== 1 ? 's' : ''} asignado{fair.inventory.length !== 1 ? 's' : ''}</p>
                  <button onClick={() => setAddingInv(true)}
                    className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all">
                    <CirclePlus className="w-4 h-4" /> Asignar inventario
                  </button>
                </div>
              )}
              {fair.inventory.length === 0 ? (
                <p className="text-center text-gray-400 text-sm py-8">No hay inventario asignado a esta feria</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        {['Producto', 'Inicial', 'Vendido', 'Remanente', '% Vendido', 'Precio ref.', ''].map(h => (
                          <th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pb-2 pr-4">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {fair.inventory.map(inv => {
                        const pct = inv.initialQuantity > 0 ? (inv.soldQuantity / inv.initialQuantity) * 100 : 0
                        return (
                          <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                            <td className="py-2.5 pr-4 font-medium text-gray-800">{inv.productName}</td>
                            <td className="py-2.5 pr-4 text-gray-600">{inv.initialQuantity}</td>
                            <td className="py-2.5 pr-4 text-emerald-700 font-semibold">{inv.soldQuantity}</td>
                            <td className="py-2.5 pr-4 text-gray-600">{inv.remainingQuantity}</td>
                            <td className="py-2.5 pr-4">
                              <div className="flex items-center gap-2">
                                <div className="w-16 bg-gray-200 rounded-full h-1.5">
                                  <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                                </div>
                                <span className="text-xs text-gray-600">{pct.toFixed(0)}%</span>
                              </div>
                            </td>
                            <td className="py-2.5 pr-4 text-gray-600">{fmtCOP(inv.unitValue)}</td>
                            <td className="py-2.5 pr-4">
                              {isOpen && isAdmin && (
                                <div className="flex gap-1">
                                  <button onClick={() => setEditingInv(inv)} className="p-1.5 rounded-lg hover:bg-gray-100"><Pencil className="w-3.5 h-3.5 text-gray-500" /></button>
                                </div>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Modals ── */}

      {addingInv && (
        <Modal
          item={{ detail_roasted_coffee_id: products[0]?.detail_id ?? 0, initial_quantity: 1, unit_value: 0 }}
          fields={addInvFields}
          onClose={() => setAddingInv(false)}
          onSave={handleAddInv}
          mode="add"
          title="inventario a feria"
        />
      )}

      {editingInv && (
        <Modal
          item={{ initial_quantity: editingInv.initialQuantity, unit_value: editingInv.unitValue }}
          fields={editInvFields}
          onClose={() => setEditingInv(null)}
          onSave={handleUpdateInv}
          onDelete={handleDeleteInv}
          mode="edit"
          title="inventario"
        />
      )}

      {(addingSale || editingSale) && (
        <FairSaleModal
          inventory={fair.inventory.filter(i => i.remainingQuantity > 0 || i.id === editingSale?.fairInventoryId)}
          initial={editingSale ?? undefined}
          isEdit={!!editingSale}
          onClose={() => { setAddingSale(false); setEditingSale(null) }}
          onSave={editingSale ? handleUpdateSale : handleAddSale}
          onDelete={editingSale ? handleDeleteSale : undefined}
        />
      )}

      {addingExp && (
        <Modal
          item={{ category: 'food', description: '', amount: 0 }}
          fields={expFields}
          onClose={() => setAddingExp(false)}
          onSave={handleAddExp}
          mode="add"
          title="gasto"
        />
      )}

      {editingExp && (
        <Modal
          item={{ category: editingExp.category, description: editingExp.description, amount: editingExp.amount }}
          fields={expFields}
          onClose={() => setEditingExp(null)}
          onSave={handleUpdateExp}
          onDelete={handleDeleteExp}
          mode="edit"
          title="gasto"
        />
      )}
    </div>
  )
}
