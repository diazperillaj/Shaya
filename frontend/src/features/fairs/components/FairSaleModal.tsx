import { useState } from 'react'
import { X, Check, Trash2, ShoppingBag } from 'lucide-react'
import type { FairInventory, FairProduct, FairSale, CreateFairSalePayload } from '../models/types'
import type { PaymentMethod } from '../../expenses/models/types'

interface Props {
  onClose: () => void
  onSave: (payload: CreateFairSalePayload) => Promise<void>
  onDelete?: () => Promise<void>
  inventory: FairInventory[]
  fairProducts: FairProduct[]
  paymentMethods: PaymentMethod[]
  initial?: FairSale
  isEdit?: boolean
}

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

// El combobox mezcla inventario (café) y productos de feria: la selección
// se codifica como "inv-{id}" | "prod-{id}".
type Selection = { kind: 'inv' | 'prod'; id: number } | null

const encode = (kind: 'inv' | 'prod', id: number) => `${kind}-${id}`
const decode = (raw: string): Selection => {
  const [kind, id] = raw.split('-')
  if ((kind !== 'inv' && kind !== 'prod') || !id) return null
  return { kind, id: Number(id) }
}

export default function FairSaleModal({ onClose, onSave, onDelete, inventory, fairProducts, paymentMethods, initial, isEdit }: Props) {
  const initialSelection = (): string => {
    if (initial?.fairProductId) return encode('prod', initial.fairProductId)
    if (initial?.fairInventoryId) return encode('inv', initial.fairInventoryId)
    if (inventory.length > 0) return encode('inv', inventory[0].id)
    if (fairProducts.length > 0) return encode('prod', fairProducts[0].id)
    return ''
  }

  const defaultUnitValue = (): number => {
    if (initial) return initial.unitValue
    if (inventory.length > 0) return inventory[0].unitValue
    if (fairProducts.length > 0) return fairProducts[0].defaultPrice
    return 0
  }

  const [selection, setSelection] = useState<string>(initialSelection)
  const [paymentMethodId, setPaymentMethodId] = useState<number>(initial?.paymentMethodId ?? 0)
  const [qty, setQty] = useState(initial?.quantity ?? 1)
  const [unitValue, setUnitValue] = useState(defaultUnitValue)
  const [observations, setObservations] = useState(initial?.observations ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const sel = decode(selection)
  const selectedInv = sel?.kind === 'inv' ? inventory.find((i) => i.id === sel.id) : undefined
  const total = qty * unitValue

  const handleSelectionChange = (raw: string) => {
    setSelection(raw)
    const s = decode(raw)
    if (s?.kind === 'inv') {
      const inv = inventory.find((i) => i.id === s.id)
      if (inv) setUnitValue(inv.unitValue)
    } else if (s?.kind === 'prod') {
      const prod = fairProducts.find((p) => p.id === s.id)
      if (prod) setUnitValue(prod.defaultPrice)
    }
    setQty(1)
  }

  const handleSave = async () => {
    if (!sel || qty < 1 || unitValue <= 0) { setError('Completa todos los campos requeridos'); return }
    if (!paymentMethodId) { setError('Selecciona el método de pago'); return }
    if (selectedInv && qty > selectedInv.remainingQuantity) {
      setError(`Stock insuficiente. Disponible: ${selectedInv.remainingQuantity} bolsas`); return
    }
    setSaving(true); setError('')
    try {
      await onSave({
        ...(sel.kind === 'inv' ? { fair_inventory_id: sel.id } : { fair_product_id: sel.id }),
        payment_method_id: paymentMethodId,
        quantity: qty,
        unit_value: unitValue,
        observations: observations.trim() || undefined,
      })
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
              value={selection}
              onChange={(e) => handleSelectionChange(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
            >
              {inventory.length > 0 && (
                <optgroup label="Inventario (café)">
                  {inventory.map((inv) => (
                    <option key={`inv-${inv.id}`} value={encode('inv', inv.id)} disabled={inv.remainingQuantity === 0}>
                      {inv.productName} — {inv.remainingQuantity} disp.
                    </option>
                  ))}
                </optgroup>
              )}
              {fairProducts.length > 0 && (
                <optgroup label="Productos">
                  {fairProducts.map((p) => (
                    <option key={`prod-${p.id}`} value={encode('prod', p.id)}>
                      {p.name} — {fmtCOP(p.defaultPrice)}
                    </option>
                  ))}
                </optgroup>
              )}
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
              <label className="text-sm font-semibold text-gray-700">Precio unit. *</label>
              <input
                type="number" min={1} value={unitValue}
                onChange={(e) => setUnitValue(Number(e.target.value))}
                className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700">Pagado con *</label>
            <select
              value={paymentMethodId || ''}
              onChange={(e) => setPaymentMethodId(Number(e.target.value))}
              className="border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
            >
              <option value="" disabled>Selecciona el método</option>
              {paymentMethods.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
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
