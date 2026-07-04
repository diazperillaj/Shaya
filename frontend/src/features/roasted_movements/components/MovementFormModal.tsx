import { useEffect, useMemo, useState } from 'react'
import { X, Check, Plus, Trash2, ArrowDownToLine, ArrowUpFromLine, Repeat } from 'lucide-react'
import type { RoastedMovementCreate, RoastedMovementDetailCreate } from '../models/types'
import { fetchRoastedCoffees } from '../../roasted_coffee/services/roasted_coffee.api'
import type { RoastedCoffeeRow } from '../../roasted_coffee/models/types'
import { fetchProducts } from '../../processes/services/inventoryProcessed.api'
import type { Product } from '../../products/models/types'

interface Props {
  onClose: () => void
  onSave: (payload: RoastedMovementCreate) => Promise<void>
}

type MovementKind = 'exit' | 'entry' | 'repack'

interface ExitRow {
  key: number
  detail_roasted_coffee_id: number
  quantity: number
}

interface EntryRow {
  key: number
  mode: 'existing' | 'new'
  detail_roasted_coffee_id: number
  product_id: number
  roasted_coffee_id: number
  quantity: number
  grams_per_bag: number
  manual_unit_cost: number
}

const KIND_OPTIONS: { value: MovementKind; label: string; icon: any; hint: string }[] = [
  { value: 'exit', label: 'Salida', icon: ArrowUpFromLine, hint: 'Sacar bolsas del inventario (envíos, bajas)' },
  { value: 'entry', label: 'Entrada', icon: ArrowDownToLine, hint: 'Agregar bolsas al inventario (ajustes, hallazgos)' },
  { value: 'repack', label: 'Reempaque', icon: Repeat, hint: 'Sacar de un lote y convertirlo en otras presentaciones' },
]

const newEntryRow = (key: number): EntryRow => ({
  key,
  mode: 'existing',
  detail_roasted_coffee_id: 0,
  product_id: 0,
  roasted_coffee_id: 0,
  quantity: 1,
  grams_per_bag: 0,
  manual_unit_cost: 0,
})

export default function MovementFormModal({ onClose, onSave }: Props) {
  const now = new Date()
  const localIso = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16)

  const [kind, setKind] = useState<MovementKind>('exit')
  const [movementDate, setMovementDate] = useState(localIso)
  const [observations, setObservations] = useState('')

  // Salidas (modo exit) / lote origen (modo repack)
  const [exitRows, setExitRows] = useState<ExitRow[]>([{ key: 0, detail_roasted_coffee_id: 0, quantity: 1 }])
  const [sourceId, setSourceId] = useState(0)
  const [sourceQty, setSourceQty] = useState(1)

  // Entradas (modos entry y repack)
  const [entryRows, setEntryRows] = useState<EntryRow[]>([newEntryRow(0)])

  const [nextKey, setNextKey] = useState(1)
  const [options, setOptions] = useState<RoastedCoffeeRow[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRoastedCoffees().then(setOptions).catch(() => setOptions([]))
    fetchProducts().then(setProducts).catch(() => setProducts([]))
  }, [])

  const available = useMemo(() => options.filter((o) => o.remaining_quantity > 0), [options])
  const source = options.find((o) => o.detail_id === sourceId)

  /** Maquilados únicos (para el destino de entradas puras de producto nuevo) */
  const maquilados = useMemo(() => {
    const ids = new Map<number, string>()
    options.forEach((o) => {
      if (!ids.has(o.maquilado_id)) ids.set(o.maquilado_id, `Maquilado #${o.maquilado_id}`)
    })
    return Array.from(ids.entries())
  }, [options])

  /** Lotes existentes válidos como destino de entrada según el modo */
  const entryTargets = () =>
    kind === 'repack' && source
      ? options.filter((o) => o.maquilado_id === source.maquilado_id && o.detail_id !== sourceId)
      : options

  const getAvailable = (detail_id: number) =>
    options.find((o) => o.detail_id === detail_id)?.remaining_quantity ?? 0

  // ── Manejo de filas ─────────────────────────────────────────────────────────

  const addExitRow = () => {
    setExitRows((prev) => [...prev, { key: nextKey, detail_roasted_coffee_id: 0, quantity: 1 }])
    setNextKey((k) => k + 1)
  }

  const addEntryRow = () => {
    setEntryRows((prev) => [...prev, newEntryRow(nextKey)])
    setNextKey((k) => k + 1)
  }

  const updateExitRow = (key: number, field: keyof Omit<ExitRow, 'key'>, value: number) =>
    setExitRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)))

  const updateEntryRow = (key: number, patch: Partial<EntryRow>) =>
    setEntryRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...patch } : r)))

  // ── Guardar ─────────────────────────────────────────────────────────────────

  const buildDetails = (): RoastedMovementDetailCreate[] | string => {
    const details: RoastedMovementDetailCreate[] = []

    if (kind === 'exit') {
      if (exitRows.length === 0) return 'Agrega al menos una salida'
      for (const r of exitRows) {
        if (!r.detail_roasted_coffee_id) return 'Selecciona un lote en cada salida'
        if (r.quantity <= 0) return 'Las cantidades deben ser mayores a 0'
        if (r.quantity > getAvailable(r.detail_roasted_coffee_id)) {
          return `Stock insuficiente (disponible: ${getAvailable(r.detail_roasted_coffee_id)})`
        }
        details.push({ detail_roasted_coffee_id: r.detail_roasted_coffee_id, quantity: r.quantity, direction: 'exit' })
      }
      return details
    }

    if (kind === 'repack') {
      if (!sourceId) return 'Selecciona el lote de origen'
      if (sourceQty <= 0) return 'La cantidad a sacar debe ser mayor a 0'
      if (sourceQty > getAvailable(sourceId)) {
        return `Stock insuficiente en el origen (disponible: ${getAvailable(sourceId)})`
      }
      details.push({ detail_roasted_coffee_id: sourceId, quantity: sourceQty, direction: 'exit' })
    }

    // Entradas (entry y repack)
    if (entryRows.length === 0) return 'Agrega al menos una entrada'
    for (const r of entryRows) {
      if (r.quantity <= 0) return 'Las cantidades deben ser mayores a 0'
      if (kind === 'repack' && (!r.grams_per_bag || r.grams_per_bag <= 0)) {
        return 'En un reempaque cada entrada necesita los gramos por bolsa'
      }
      if (r.mode === 'existing') {
        if (!r.detail_roasted_coffee_id) return 'Selecciona el lote destino en cada entrada'
        details.push({
          detail_roasted_coffee_id: r.detail_roasted_coffee_id,
          quantity: r.quantity,
          direction: 'entry',
          ...(kind === 'repack' ? { grams_per_bag: r.grams_per_bag } : {}),
        })
      } else {
        if (!r.product_id) return 'Selecciona el producto en cada entrada nueva'
        if (kind === 'entry' && !r.roasted_coffee_id) return 'Selecciona el maquilado destino del producto nuevo'
        details.push({
          product_id: r.product_id,
          quantity: r.quantity,
          direction: 'entry',
          ...(kind === 'repack' ? { grams_per_bag: r.grams_per_bag } : {}),
          ...(kind === 'entry' ? { roasted_coffee_id: r.roasted_coffee_id } : {}),
          ...(kind === 'entry' && r.manual_unit_cost > 0 ? { manual_unit_cost: r.manual_unit_cost } : {}),
        })
      }
    }
    return details
  }

  const handleSave = async () => {
    setError(null)
    if (!movementDate) { setError('La fecha es obligatoria'); return }

    const details = buildDetails()
    if (typeof details === 'string') { setError(details); return }

    setSaving(true)
    try {
      await onSave({
        movement_date: new Date(movementDate).toISOString(),
        observations: observations || undefined,
        details,
      })
    } catch (e: any) {
      setError(e.message ?? 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  const inputCls = 'text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white'

  const lotSelect = (
    value: number,
    onChange: (v: number) => void,
    rows: RoastedCoffeeRow[],
    placeholder = 'Seleccionar lote…',
  ) => (
    <select value={value || ''} onChange={(e) => onChange(Number(e.target.value))} className={`${inputCls} w-full`}>
      <option value="">{placeholder}</option>
      {rows.map((o) => (
        <option key={o.detail_id} value={o.detail_id}>
          Lote #{o.maquilado_id} — {o.product_name} (disp: {o.remaining_quantity})
        </option>
      ))}
    </select>
  )

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between flex-shrink-0">
          <h2 className="text-lg font-semibold text-white">Nuevo movimiento</h2>
          <button onClick={onClose} className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex flex-col gap-4 overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">

          {/* Tipo de movimiento */}
          <div className="grid grid-cols-3 gap-2">
            {KIND_OPTIONS.map((k) => {
              const Icon = k.icon
              const active = kind === k.value
              return (
                <button
                  key={k.value}
                  onClick={() => { setKind(k.value); setError(null) }}
                  className={`flex flex-col items-center gap-1 px-3 py-3 rounded-xl border text-sm font-medium transition-all ${
                    active
                      ? 'bg-emerald-900 border-emerald-900 text-white shadow-md'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {k.label}
                </button>
              )
            })}
          </div>
          <p className="text-xs text-gray-400 -mt-2 ps-1">{KIND_OPTIONS.find((k) => k.value === kind)?.hint}</p>

          {/* Fecha + Observaciones */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700 ps-1">Fecha</label>
            <input type="datetime-local" value={movementDate} onChange={(e) => setMovementDate(e.target.value)} className={inputCls} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-gray-700 ps-1">Observaciones</label>
            <textarea
              value={observations}
              onChange={(e) => setObservations(e.target.value)}
              rows={2}
              placeholder="Descripción del movimiento…"
              className={`${inputCls} resize-none`}
            />
          </div>

          {/* ── SALIDAS (modo exit) ── */}
          {kind === 'exit' && (
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-gray-700 ps-1">Lotes a sacar</label>
              {exitRows.map((row) => (
                <div key={row.key} className="flex gap-2 items-center">
                  <div className="flex-1">{lotSelect(row.detail_roasted_coffee_id, (v) => updateExitRow(row.key, 'detail_roasted_coffee_id', v), available)}</div>
                  <input
                    type="number" min={1} value={row.quantity}
                    onChange={(e) => updateExitRow(row.key, 'quantity', Number(e.target.value))}
                    className={`${inputCls} w-24 text-center`}
                  />
                  <button
                    onClick={() => setExitRows((p) => p.filter((r) => r.key !== row.key))}
                    disabled={exitRows.length === 1}
                    className="p-2.5 rounded-xl text-red-400 hover:text-red-600 hover:bg-red-50 transition-all disabled:opacity-30"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              <button onClick={addExitRow} className="flex items-center gap-2 text-sm text-emerald-700 hover:text-emerald-900 font-medium px-2 py-1.5 rounded-lg hover:bg-emerald-50 transition-all w-fit">
                <Plus className="w-4 h-4" /> Agregar lote
              </button>
            </div>
          )}

          {/* ── LOTE DE ORIGEN (modo repack) ── */}
          {kind === 'repack' && (
            <div className="flex flex-col gap-2 bg-red-50/50 border border-red-100 rounded-xl p-3">
              <label className="text-sm font-semibold text-gray-700 ps-1">Lote de origen (se saca)</label>
              <div className="flex gap-2 items-center">
                <div className="flex-1">{lotSelect(sourceId, (v) => { setSourceId(v); setEntryRows([newEntryRow(nextKey)]); setNextKey((k) => k + 1) }, available, 'Seleccionar lote de origen…')}</div>
                <input
                  type="number" min={1} max={getAvailable(sourceId) || undefined} value={sourceQty}
                  onChange={(e) => setSourceQty(Number(e.target.value))}
                  className={`${inputCls} w-24 text-center`}
                />
              </div>
              {sourceId > 0 && (
                <span className="text-xs text-gray-400 ps-1">
                  Disponible: {getAvailable(sourceId)} und · Las entradas quedan en el mismo maquilado #{source?.maquilado_id}
                </span>
              )}
            </div>
          )}

          {/* ── ENTRADAS (modos entry y repack) ── */}
          {(kind === 'entry' || kind === 'repack') && (
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-gray-700 ps-1">
                {kind === 'repack' ? 'Entradas (lo que se reempaca)' : 'Entradas'}
              </label>
              {entryRows.map((row) => (
                <div key={row.key} className="flex flex-col gap-2 bg-emerald-50/40 border border-emerald-100 rounded-xl p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-0.5">
                      {(['existing', 'new'] as const).map((m) => (
                        <button
                          key={m}
                          onClick={() => updateEntryRow(row.key, { mode: m })}
                          className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                            row.mode === m ? 'bg-emerald-900 text-white' : 'text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {m === 'existing' ? 'Lote existente' : 'Producto nuevo'}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={() => setEntryRows((p) => p.filter((r) => r.key !== row.key))}
                      disabled={entryRows.length === 1}
                      className="p-1.5 rounded-lg text-red-400 hover:text-red-600 hover:bg-red-50 transition-all disabled:opacity-30"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {row.mode === 'existing' ? (
                    lotSelect(row.detail_roasted_coffee_id, (v) => updateEntryRow(row.key, { detail_roasted_coffee_id: v }), entryTargets(), 'Lote destino…')
                  ) : (
                    <div className="flex flex-col gap-2">
                      {kind === 'entry' && (
                        <select
                          value={row.roasted_coffee_id || ''}
                          onChange={(e) => updateEntryRow(row.key, { roasted_coffee_id: Number(e.target.value) })}
                          className={inputCls}
                        >
                          <option value="">Maquilado destino…</option>
                          {maquilados.map(([id, label]) => (
                            <option key={id} value={id}>{label}</option>
                          ))}
                        </select>
                      )}
                      <select
                        value={row.product_id || ''}
                        onChange={(e) => updateEntryRow(row.key, { product_id: Number(e.target.value) })}
                        className={inputCls}
                      >
                        <option value="">Producto…</option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <div className="flex-1 flex flex-col gap-1">
                      <span className="text-xs text-gray-400 ps-1">Cantidad (bolsas)</span>
                      <input
                        type="number" min={1} value={row.quantity}
                        onChange={(e) => updateEntryRow(row.key, { quantity: Number(e.target.value) })}
                        className={`${inputCls} text-center`}
                      />
                    </div>
                    {kind === 'repack' && (
                      <div className="flex-1 flex flex-col gap-1">
                        <span className="text-xs text-gray-400 ps-1">Gramos por bolsa</span>
                        <input
                          type="number" min={1} value={row.grams_per_bag || ''}
                          placeholder="ej. 125"
                          onChange={(e) => updateEntryRow(row.key, { grams_per_bag: Number(e.target.value) })}
                          className={`${inputCls} text-center`}
                        />
                      </div>
                    )}
                    {kind === 'entry' && row.mode === 'new' && (
                      <div className="flex-1 flex flex-col gap-1">
                        <span className="text-xs text-gray-400 ps-1">Costo/bolsa (opcional)</span>
                        <input
                          type="number" min={0} value={row.manual_unit_cost || ''}
                          placeholder="Sin costo"
                          onChange={(e) => updateEntryRow(row.key, { manual_unit_cost: Number(e.target.value) })}
                          className={`${inputCls} text-center`}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <button onClick={addEntryRow} className="flex items-center gap-2 text-sm text-emerald-700 hover:text-emerald-900 font-medium px-2 py-1.5 rounded-lg hover:bg-emerald-50 transition-all w-fit">
                <Plus className="w-4 h-4" /> Agregar entrada
              </button>
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2.5">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex justify-end gap-3 flex-shrink-0">
          <button
            onClick={onClose}
            className="bg-white hover:bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium border border-gray-200 flex items-center gap-2 transition-all"
          >
            <X className="w-4 h-4" /> Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl font-medium shadow-md flex items-center gap-2 transition-all disabled:opacity-60"
          >
            <Check className="w-4 h-4" /> {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  )
}
