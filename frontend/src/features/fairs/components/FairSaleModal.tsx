import { useState } from 'react'
import { X, Check, Trash2, ShoppingBag } from 'lucide-react'
import type { FairInventory, FairSale, CreateFairSalePayload } from '../models/types'

interface Props {
  onClose: () => void
  onSave: (payload: CreateFairSalePayload) => Promise<void>
  onDelete?: () => Promise<void>
  inventory: FairInventory[]
  initial?: FairSale
  isEdit?: boolean
}

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

export default function FairSaleModal({ onClose, onSave, onDelete, inventory, initial, isEdit }: Props) {
  const defaultInv = inventory[0]
  const [invId, setInvId] = useState<number>(initial?.fairInventoryId ?? defaultInv?.id ?? 0)
  const [qty, setQty] = useState(initial?.quantity ?? 1)
  const [unitValue, setUnitValue] = useState(initial?.unitValue ?? defaultInv?.unitValue ?? 0)
  const [observations, setObservations] = useState(initial?.observations ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const selectedInv = inventory.find((i) => i.id === invId)
  const total = qty * unitValue

  const handleInvChange = (id: number) => {
    setInvId(id)
    const inv = inventory.find((i) => i.id === id)
    if (inv) setUnitValue(inv.unitValue)
    setQty(1)
  }

  const handleSave = async () => {
    if (!invId || qty < 1 || unitValue <= 0) { setError('Completa todos los campos requeridos'); return }
    if (selectedInv && qty > selectedInv.remainingQuantity) {
      setError(`Stock insuficiente. Disponible: ${selectedInv.remainingQuantity} bolsas`); return
    }
    setSaving(true); setError('')
    try {
      await onSave({ fair_inventory_id: invId, quantity: qty, unit_value: unitValue, observations: observations.trim() || undefined })
      onClose()
    } catch (e: any) { setError(e.message) }
    finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (!onDelete || !confirm('¿Eliminar esta venta? El inventario será restaurado.')) return
    setSaving(true)
    try { await onDelete(); onClose() }
    catch (e: any) { setError(e.message) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <ShoppingBag className="w-5 h-5" />
            {isEdit ? 'Editar venta' : 'Venta rápida'}
          </h2>
          <button onClick={onClose} className="text-white/80 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-all">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 flex flex-col gap-4">
          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">{error}</p>}

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">Producto *</label>
            <select
              value={invId}
              onChange={(e) => handleInvChange(Number(e.target.value))}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
            >
              {inventory.map((inv) => (
                <option key={inv.id} value={inv.id} disabled={inv.remainingQuantity === 0}>
                  {inv.productName} — {inv.remainingQuantity} disp.
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700">Cantidad *</label>
              <input
                type="number" min={1} max={selectedInv?.remainingQuantity} value={qty}
                onChange={(e) => setQty(Number(e.target.value))}
                className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 text-center text-lg font-bold"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-gray-700">Precio / bolsa *</label>
              <input
                type="number" min={1} value={unitValue}
                onChange={(e) => setUnitValue(Number(e.target.value))}
                className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
              />
            </div>
          </div>

          {total > 0 && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-center">
              <p className="text-xs text-emerald-600 font-medium uppercase tracking-wide">Total de la venta</p>
              <p className="text-2xl font-bold text-emerald-900">{fmtCOP(total)}</p>
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">Observaciones</label>
            <input
              value={observations} onChange={(e) => setObservations(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
              placeholder="Opcional…"
            />
          </div>
        </div>

        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex justify-end gap-3">
          {isEdit && onDelete && (
            <button onClick={handleDelete} disabled={saving}
              className="flex items-center gap-2 bg-red-700 hover:bg-red-800 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50">
              <Trash2 className="w-4 h-4" /> Eliminar
            </button>
          )}
          <button onClick={onClose}
            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-5 py-2.5 rounded-xl text-sm font-medium transition-all">
            <X className="w-4 h-4" /> Cancelar
          </button>
          <button onClick={handleSave} disabled={saving}
            className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50">
            <Check className="w-4 h-4" /> {saving ? 'Registrando…' : 'Registrar'}
          </button>
        </div>
      </div>
    </div>
  )
}
