import { useEffect, useState } from 'react'
import { X, ShoppingCart, Plus, Trash2, Save, PackagePlus } from 'lucide-react'
import type {
  Sale,
  SaleDetail,
  SaleStatus,
  RoastedCoffeeProduct,
  CreateSalePayload,
  CreateSaleDetailPayload,
} from '../models/types'
import type { Customer } from '../../customers/models/types'
import type { User } from '../../users/models/types'
import type { PaymentMethod } from '../../expenses/models/types'

// ─── Types ────────────────────────────────────────────────────────────────────

interface SaleFormModalProps {
  onClose: () => void
  onSave: (payload: CreateSalePayload) => Promise<void>
  onDelete?: () => Promise<void>
  customers: Customer[]
  users: User[]
  products: RoastedCoffeeProduct[]
  paymentMethods: PaymentMethod[]
  initialSale?: Sale
  initialDetails?: SaleDetail[]
  isEdit?: boolean
  isAdmin?: boolean
}

interface DetailRow extends CreateSaleDetailPayload {
  _key: number
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

let _keyCounter = 0
const nextKey = () => ++_keyCounter

const emptyDetail = (): DetailRow => ({
  _key: nextKey(),
  detail_roasted_coffee_id: 0,
  quantity: 0,
  unit_value: 0,
  iva_percentage: 0,
})

const fmtCOP = (n: number): string =>
  n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })

// ─── Component ───────────────────────────────────────────────────────────────

export default function SaleFormModal({
  onClose,
  onSave,
  onDelete,
  customers,
  users,
  products,
  paymentMethods,
  initialSale,
  initialDetails = [],
  isEdit = false,
  isAdmin = false,
}: SaleFormModalProps) {
  // ── Header state ────────────────────────────────────────────────────────────
  const [customerId, setCustomerId] = useState('')
  const [userId, setUserId] = useState('')
  const [paymentMethodId, setPaymentMethodId] = useState('')
  const [saleDate, setSaleDate] = useState('')
  const [status, setStatus] = useState<SaleStatus>('in_progress')
  const [observations, setObservations] = useState('')

  // ── Detail lines ────────────────────────────────────────────────────────────
  const [details, setDetails] = useState<DetailRow[]>([emptyDetail()])

  // Cantidades que esta venta ya tiene descontadas por lote: al editar,
  // esas unidades vuelven a estar disponibles (evita el falso "stock 0").
  const originalQty: Record<number, number> = {}
  for (const d of initialDetails) {
    originalQty[d.detail_roasted_coffee_id] =
      (originalQty[d.detail_roasted_coffee_id] ?? 0) + d.quantity
  }

  // En el select solo se ocultan lotes agotados que NO son de esta venta
  const selectableProducts = products.filter(
    (p) => p.remaining_quantity > 0 || originalQty[p.detail_id],
  )

  // ── Prefill when editing ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!initialSale) return
    setCustomerId(String(initialSale.customer_id))
    setUserId(String(initialSale.user_id))
    setPaymentMethodId(initialSale.payment_method_id ? String(initialSale.payment_method_id) : '')
    setSaleDate(initialSale.sale_date)
    setStatus(initialSale.status)
    setObservations(initialSale.observations ?? '')

    if (initialDetails.length > 0) {
      setDetails(
        initialDetails.map((d) => ({
          _key: nextKey(),
          detail_roasted_coffee_id: d.detail_roasted_coffee_id,
          quantity: d.quantity,
          unit_value: d.unit_value,
          iva_percentage: d.iva_percentage,
        })),
      )
    }
  }, [initialSale, initialDetails])

  // ── Derived financials ──────────────────────────────────────────────────────
  const totals = details.reduce(
    (acc, d) => {
      const sub = d.quantity * d.unit_value
      const iva = sub * (d.iva_percentage / 100)
      return { subtotal: acc.subtotal + sub, iva: acc.iva + iva }
    },
    { subtotal: 0, iva: 0 },
  )
  const grandTotal = totals.subtotal + totals.iva

  // ── Saving ──────────────────────────────────────────────────────────────────
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    if (!customerId) return setError('Selecciona un cliente.')
    if (!paymentMethodId) return setError('Selecciona un método de pago.')
    if (!saleDate) return setError('La fecha es requerida.')
    if (details.length === 0) return setError('Agrega al menos un producto.')
    if (details.some((d) => !d.detail_roasted_coffee_id))
      return setError('Todos los detalles deben tener un producto seleccionado.')
    if (details.some((d) => d.quantity <= 0))
      return setError('La cantidad debe ser mayor a 0 en todos los detalles.')
    if (details.some((d) => d.unit_value <= 0))
      return setError('El valor unitario debe ser mayor a 0 en todos los detalles.')

    setError(null)
    setSaving(true)
    try {
      const payload: CreateSalePayload = {
        customer_id: parseInt(customerId),
        user_id: isAdmin && userId ? parseInt(userId) : undefined,
        payment_method_id: parseInt(paymentMethodId),
        sale_date: saleDate,
        status,
        observations: observations.trim() || undefined,
        details: details.map(({ _key, ...d }) => d),
      }
      await onSave(payload)
    } catch (err: any) {
      setError(err.message || 'Error al guardar la venta.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!onDelete) return
    const confirmed = window.confirm(
      'Esta acción borrará la venta y restaurará el inventario. ¿Deseas continuar?',
    )
    if (!confirmed) return

    setError(null)
    setDeleting(true)
    try {
      await onDelete()
    } catch (err: any) {
      setError(err.message || 'Error al borrar la venta.')
    } finally {
      setDeleting(false)
    }
  }

  // ── Detail helpers ──────────────────────────────────────────────────────────
  const addDetail = () => setDetails((prev) => [...prev, emptyDetail()])

  const removeDetail = (key: number) =>
    setDetails((prev) => prev.filter((d) => d._key !== key))

  const updateDetail = <K extends keyof DetailRow>(
    key: number,
    field: K,
    value: DetailRow[K],
  ) =>
    setDetails((prev) =>
      prev.map((d) => (d._key === key ? { ...d, [field]: value } : d)),
    )

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[95vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between flex-shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <ShoppingCart className="w-5 h-5 flex-shrink-0" />
            {isEdit ? 'Editar venta' : 'Nueva venta'}
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all duration-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 p-6 space-y-7 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">

          {/* ── Section 1: Datos de la venta ──────────────────────────────── */}
          <section>
            <SectionTitle label="Datos de la venta" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">

              <FormField label="Cliente" required>
                <select
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className={inputCls}
                >
                  <option value="" disabled>Selecciona un cliente</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} — {c.city}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField label="Fecha" required>
                <input
                  type="date"
                  value={saleDate}
                  onChange={(e) => setSaleDate(e.target.value)}
                  className={inputCls}
                />
              </FormField>

              <FormField label="Método de pago" required>
                <select
                  value={paymentMethodId}
                  onChange={(e) => setPaymentMethodId(e.target.value)}
                  className={inputCls}
                >
                  <option value="" disabled>Selecciona un método</option>
                  {paymentMethods.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </FormField>

              <FormField label="Estado" required>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as SaleStatus)}
                  className={inputCls}
                >
                  <option value="in_progress">En progreso</option>
                  <option value="completed">Completada</option>
                </select>
              </FormField>

              {isAdmin && (
                <FormField label="Asignar a vendedor">
                  <select
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    className={inputCls}
                  >
                    <option value="">Vendedor actual (por defecto)</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name} ({u.username})
                      </option>
                    ))}
                  </select>
                </FormField>
              )}
            </div>

            <div className="mt-4">
              <FormField label="Observaciones">
                <textarea
                  value={observations}
                  onChange={(e) => setObservations(e.target.value)}
                  rows={2}
                  placeholder="Observaciones de la venta (opcional)"
                  className={`${inputCls} resize-none`}
                />
              </FormField>
            </div>
          </section>

          {/* ── Section 2: Resumen financiero ─────────────────────────────── */}
          <section>
            <SectionTitle label="Resumen financiero (calculado)" />
            <div className="grid grid-cols-3 gap-3">
              <FinanceCard label="Subtotal" value={fmtCOP(totals.subtotal)} />
              <FinanceCard label="IVA" value={fmtCOP(totals.iva)} />
              <FinanceCard label="Total" value={fmtCOP(grandTotal)} highlight />
            </div>
          </section>

          {/* ── Section 3: Detalle de productos ───────────────────────────── */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <PackagePlus className="w-4 h-4 text-emerald-700" />
                <span className="text-sm font-semibold text-emerald-800 uppercase tracking-wider">
                  Productos
                </span>
                <span className="bg-emerald-800 text-white text-xs font-bold rounded-full px-2 py-0.5">
                  {details.length}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {details.map((det, idx) => (
                <DetailLine
                  key={det._key}
                  index={idx}
                  detail={det}
                  onChange={(field, value) => updateDetail(det._key, field, value)}
                  onRemove={() => removeDetail(det._key)}
                  canRemove={details.length > 1}
                  products={selectableProducts}
                  originalQty={originalQty}
                />
              ))}
            </div>

            <button
              onClick={addDetail}
              className="flex items-center m-5 gap-1.5 text-sm bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-2 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200"
            >
              <Plus className="w-4 h-4" />
              Agregar producto
            </button>
          </section>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex-shrink-0 flex justify-between items-center gap-3">
          <div className="flex items-center gap-2">
            {isEdit && onDelete && (
              <button
                onClick={handleDelete}
                disabled={deleting || saving}
                className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:opacity-60 text-white px-5 py-2.5 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200"
              >
                <Trash2 className="w-4 h-4" />
                {deleting ? 'Borrando...' : 'Borrar'}
              </button>
            )}
            <button
              onClick={onClose}
              className="flex items-center gap-2 bg-white hover:bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 border border-gray-200"
            >
              <X className="w-4 h-4" />
              Cancelar
            </button>
          </div>

          <button
            onClick={handleSave}
            disabled={saving || deleting}
            className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 disabled:opacity-60 text-white px-6 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
          >
            {saving ? (
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {isEdit ? 'Actualizar venta' : 'Guardar venta'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── DetailLine ───────────────────────────────────────────────────────────────

interface DetailLineProps {
  index: number
  detail: DetailRow
  onChange: <K extends keyof DetailRow>(field: K, value: DetailRow[K]) => void
  onRemove: () => void
  canRemove: boolean
  products: RoastedCoffeeProduct[]
  /** Unidades ya descontadas por esta venta, por detail_roasted_coffee_id */
  originalQty: Record<number, number>
}

function DetailLine({
  index,
  detail,
  onChange,
  onRemove,
  canRemove,
  products,
  originalQty,
}: DetailLineProps) {
  const lineSub = detail.quantity * detail.unit_value
  const lineIva = lineSub * (detail.iva_percentage / 100)
  const lineTotal = lineSub + lineIva

  const selectedProduct = products.find(
    (p) => p.detail_id === detail.detail_roasted_coffee_id,
  )

  // Disponible efectivo = stock actual + lo que esta venta ya tiene reservado
  const availableFor = (p: RoastedCoffeeProduct) =>
    p.remaining_quantity + (originalQty[p.detail_id] ?? 0)
  const selectedAvailable = selectedProduct
    ? availableFor(selectedProduct)
    : undefined

  return (
    <div className="bg-gray-50 border border-gray-100 rounded-2xl p-4 space-y-3">
      {/* Row header */}
      <div className="flex items-center justify-between">
        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
          {index + 1}
        </span>
        {canRemove && (
          <button
            onClick={onRemove}
            className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg px-2 py-1 transition-all duration-200"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Eliminar
          </button>
        )}
      </div>

      {/* Fields grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="col-span-2 lg:col-span-1">
          <FormField label="Producto" required>
            <select
              value={detail.detail_roasted_coffee_id || ''}
              onChange={(e) =>
                onChange('detail_roasted_coffee_id', Number(e.target.value))
              }
              className={inputCls}
            >
              <option value="" disabled>Selecciona un producto</option>
              {products.map((p) => (
                <option key={p.detail_id} value={p.detail_id}>
                  {p.name} — {availableFor(p)} disponibles
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField label="Cantidad" required>
          <input
            type="number"
            min={1}
            max={selectedAvailable}
            value={detail.quantity || ''}
            onChange={(e) => onChange('quantity', Number(e.target.value))}
            placeholder="0"
            className={inputCls}
          />
        </FormField>

        <FormField label="Valor unitario" required>
          <input
            type="number"
            min={0}
            step={0.01}
            value={detail.unit_value || ''}
            onChange={(e) => onChange('unit_value', Number(e.target.value))}
            placeholder="0"
            className={inputCls}
          />
        </FormField>

        <FormField label="IVA (%)">
          <input
            type="number"
            min={0}
            max={100}
            step={0.1}
            value={detail.iva_percentage || ''}
            onChange={(e) => onChange('iva_percentage', Number(e.target.value))}
            placeholder="0"
            className={inputCls}
          />
        </FormField>

        {selectedProduct && (
          <FormField label="Disponibles">
            <div className={readonlyCls}>{selectedAvailable}</div>
          </FormField>
        )}
      </div>

      {/* Line totals */}
      <div className="flex flex-wrap gap-3 pt-1">
        <Badge label="Subtotal" value={fmtCOP(lineSub)} />
        <Badge label="IVA" value={fmtCOP(lineIva)} />
        <Badge label="Total línea" value={fmtCOP(lineTotal)} accent />
      </div>
    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionTitle({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="h-px flex-1 bg-emerald-100" />
      <span className="text-xs font-semibold text-emerald-700 uppercase tracking-widest whitespace-nowrap">
        {label}
      </span>
      <div className="h-px flex-1 bg-emerald-100" />
    </div>
  )
}

function FormField({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}

function FinanceCard({
  label,
  value,
  highlight = false,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div
      className={`flex flex-col items-center gap-1 rounded-xl py-4 px-3 border ${
        highlight
          ? 'bg-emerald-900 border-emerald-800 text-white'
          : 'bg-emerald-50 border-emerald-100'
      }`}
    >
      <span
        className={`text-xs font-medium uppercase tracking-wide ${
          highlight ? 'text-emerald-200' : 'text-emerald-600'
        }`}
      >
        {label}
      </span>
      <span
        className={`text-base font-bold ${highlight ? 'text-white' : 'text-emerald-900'}`}
      >
        {value}
      </span>
    </div>
  )
}

function Badge({
  label,
  value,
  accent = false,
}: {
  label: string
  value: string
  accent?: boolean
}) {
  return (
    <div
      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs border ${
        accent
          ? 'bg-emerald-100 border-emerald-200 text-emerald-800 font-bold'
          : 'bg-white border-gray-200 text-gray-600'
      }`}
    >
      <span className="font-medium">{label}:</span>
      <span>{value}</span>
    </div>
  )
}

// ─── Shared styles ────────────────────────────────────────────────────────────

const inputCls =
  'w-full text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-900 focus:border-transparent transition-all duration-200 hover:border-emerald-900 bg-white'

const readonlyCls =
  'w-full text-sm border border-gray-100 rounded-xl px-3 py-2.5 bg-gray-50 text-gray-500 font-medium'
