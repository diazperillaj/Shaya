import { useState } from 'react'
import { useEscapeKey } from '../../../hooks/useEscapeKey'
import { X, Check, Trash2, Receipt } from 'lucide-react'
import type {
  ExpenseCategory,
  GeneralExpense,
  PaymentMethod,
  UpdateExpensePayload,
} from '../models/types'

interface ExpenseFormModalProps {
  onClose: () => void
  onSave: (payload: UpdateExpensePayload) => Promise<void>
  onDelete?: () => Promise<void>
  categories: ExpenseCategory[]
  paymentMethods: PaymentMethod[]
  initial?: GeneralExpense
  isEdit?: boolean
}

const inputCls =
  'w-full text-sm border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/25 bg-white'

export default function ExpenseFormModal({
  onClose,
  onSave,
  onDelete,
  categories,
  paymentMethods,
  initial,
  isEdit = false,
}: ExpenseFormModalProps) {
  useEscapeKey(onClose)
  const [expenseDate, setExpenseDate] = useState(initial?.expense_date ?? '')
  const [amount, setAmount] = useState<number>(initial?.amount ?? 0)
  const [categoryId, setCategoryId] = useState<string>(
    initial?.category_id ? String(initial.category_id) : '',
  )
  const [paymentMethodId, setPaymentMethodId] = useState<string>(
    initial?.payment_method_id ? String(initial.payment_method_id) : '',
  )
  const [description, setDescription] = useState(initial?.description ?? '')

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSave = async () => {
    if (!expenseDate) return setError('La fecha es requerida.')
    if (!amount || amount <= 0) return setError('El valor debe ser mayor a 0.')
    if (!categoryId) return setError('Selecciona una categoría.')
    if (!description.trim()) return setError('El motivo es requerido.')

    setError('')
    setSaving(true)
    try {
      await onSave({
        expense_date: expenseDate,
        amount,
        category_id: parseInt(categoryId),
        payment_method_id: paymentMethodId ? parseInt(paymentMethodId) : undefined,
        // Al editar y quitar el método, hay que limpiarlo explícitamente
        clear_payment_method: isEdit && !paymentMethodId ? true : undefined,
        description: description.trim(),
      })
      onClose()
    } catch (e: any) {
      setError(e.message || 'Error al guardar el gasto.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!onDelete) return
    if (!window.confirm('¿Eliminar este gasto?')) return
    setSaving(true)
    try {
      await onDelete()
      onClose()
    } catch (e: any) {
      setError(e.message || 'Error al eliminar el gasto.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4 animate-fadeIn">
      <div role="dialog" aria-modal="true" className="bg-white rounded-2xl shadow-2xl w-full max-w-md text-left animate-slideUp dark:ring-1 dark:ring-white/10">
        {/* Header */}
        <div className="bg-emerald-900 dark:bg-emerald-950 rounded-t-2xl px-6 py-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <Receipt className="w-5 h-5" />
            {isEdit ? 'Editar gasto' : 'Nuevo gasto'}
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition duration-150 ease-out"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex flex-col gap-4">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">
              {error}
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700">Fecha *</label>
              <input
                type="date"
                value={expenseDate}
                onChange={(e) => setExpenseDate(e.target.value)}
                className={inputCls}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700">Valor *</label>
              <input
                type="number"
                min={0}
                value={amount || ''}
                onChange={(e) => setAmount(Number(e.target.value))}
                placeholder="0"
                className={inputCls}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">Categoría *</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className={inputCls}
            >
              <option value="" disabled>Selecciona una categoría</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">Pagado con</label>
            <select
              value={paymentMethodId}
              onChange={(e) => setPaymentMethodId(e.target.value)}
              className={inputCls}
            >
              <option value="">Sin especificar</option>
              {paymentMethods.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">Motivo *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              placeholder="¿En qué se gastó?"
              className={`${inputCls} resize-none`}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex justify-end gap-3">
          {isEdit && onDelete && (
            <button
              onClick={handleDelete}
              disabled={saving}
              className="flex items-center gap-2 bg-red-700 hover:bg-red-800 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition duration-150 ease-out"
            >
              <Trash2 className="w-4 h-4" /> Eliminar
            </button>
          )}
          <button
            onClick={onClose}
            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-5 py-2.5 rounded-xl text-sm font-medium transition duration-150 ease-out"
          >
            <X className="w-4 h-4" /> Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 disabled:opacity-50 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition duration-150 ease-out"
          >
            <Check className="w-4 h-4" /> {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  )
}
