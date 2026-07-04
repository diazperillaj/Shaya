// src/features/products/components/ProductExpensesModal.tsx
import { useEffect, useState } from 'react'
import { X, Coins, CirclePlus, Info } from 'lucide-react'

import DataTable from '../../../components/ui/DataTable'
import Modal from '../../../components/ui/Modal'
import { runWithAlert } from '../../../hooks/useSafeAction'
import { useAuth } from '../../auth/AuthContext'

import type { Product, ProductExpense } from '../models/types'
import { ProductExpenseColumns } from '../models/columns'
import { ProductExpenseFields } from '../models/fields'
import {
  fetchProductExpenses,
  createProductExpense,
  updateProductExpense,
  deleteProductExpense,
} from '../services/productExpenses.api'

interface ProductExpensesModalProps {
  product: Product
  onClose: () => void
}

/**
 * Modal de costos de producción por bolsa de un producto
 * (empaque, etiqueta, insumos, etc.).
 *
 * Los cambios aplican solo a procesos futuros: los lotes ya
 * producidos conservan su costo histórico.
 */
export default function ProductExpensesModal({
  product,
  onClose,
}: ProductExpensesModalProps) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [expenses, setExpenses] = useState<ProductExpense[]>([])
  const [loading, setLoading] = useState(true)
  const [addingExpense, setAddingExpense] = useState(false)
  const [editingExpense, setEditingExpense] = useState<ProductExpense | null>(null)

  const loadExpenses = async (): Promise<void> => {
    setLoading(true)
    try {
      setExpenses(await fetchProductExpenses(product.id))
    } catch {
      setExpenses([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadExpenses()
  }, [product.id])

  const emptyExpense: ProductExpense = {
    id: 0,
    product_id: product.id,
    category: 'packaging',
    amount: 0,
    observations: '',
  }

  const handleSaveExpense = async (expense: ProductExpense): Promise<void> => {
    if (!expense.amount || expense.amount <= 0) {
      alert('El valor por bolsa debe ser mayor a 0')
      return
    }
    const payload = {
      category: expense.category,
      amount: expense.amount,
      observations: expense.observations || undefined,
    }
    await runWithAlert(async () => {
      if (expense.id) {
        await updateProductExpense(expense.id, payload)
      } else {
        await createProductExpense(product.id, payload)
      }
      setAddingExpense(false)
      setEditingExpense(null)
      await loadExpenses()
    }, expense.id ? 'Costo actualizado correctamente' : 'Costo agregado correctamente')
  }

  const handleDeleteExpense = async (expense: ProductExpense): Promise<void> => {
    if (!window.confirm('¿Eliminar este costo de producción?')) return
    await runWithAlert(async () => {
      await deleteProductExpense(expense.id)
      await loadExpenses()
    }, 'Costo eliminado correctamente')
  }

  const totalPerBag = expenses.reduce((sum, e) => sum + e.amount, 0)

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">

        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between flex-shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <Coins className="w-5 h-5 flex-shrink-0" />
            Costos de producción — {product.name}
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all duration-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Body ────────────────────────────────────────────────────────── */}
        <div className="overflow-y-auto flex-1 p-6 space-y-4 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">

          <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800">
            <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>
              Estos costos se suman al costo unitario de cada bolsa en los
              <span className="font-semibold"> procesos futuros</span>. Los lotes
              ya producidos conservan su costo histórico.
            </p>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Total por bolsa:{' '}
              <span className="font-semibold text-emerald-900">
                {totalPerBag.toLocaleString('es-CO', {
                  style: 'currency',
                  currency: 'COP',
                  maximumFractionDigits: 0,
                })}
              </span>
            </p>
            <button
              onClick={() => setAddingExpense(true)}
              className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all"
            >
              <CirclePlus className="w-4 h-4" /> Agregar costo
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center items-center py-8 text-emerald-700 text-sm gap-2">
              <span className="animate-spin inline-block w-4 h-4 border-2 border-emerald-700 border-t-transparent rounded-full" />
              Cargando costos…
            </div>
          ) : (
            <DataTable
              columns={ProductExpenseColumns}
              data={expenses}
              isAdmin={true}
              onEdit={setEditingExpense}
              onDelete={isAdmin ? handleDeleteExpense : undefined}
              showPagination={false}
              emptyMessage="Sin costos registrados. Agrega empaque, etiqueta, etc."
            />
          )}
        </div>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex-shrink-0 flex justify-end">
          <button
            onClick={onClose}
            className="flex items-center gap-2 bg-white hover:bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 border border-gray-200"
          >
            <X className="w-4 h-4" />
            Cerrar
          </button>
        </div>
      </div>

      {/* ── Formulario de costo (modal anidado) ─────────────────────────────── */}
      {addingExpense && (
        <Modal
          item={emptyExpense}
          fields={ProductExpenseFields}
          onClose={() => setAddingExpense(false)}
          onSave={handleSaveExpense}
          mode="add"
          title="costo de producción"
        />
      )}

      {editingExpense && (
        <Modal
          item={editingExpense}
          fields={ProductExpenseFields}
          onClose={() => setEditingExpense(null)}
          onSave={handleSaveExpense}
          mode="edit"
          title="costo de producción"
        />
      )}
    </div>
  )
}
