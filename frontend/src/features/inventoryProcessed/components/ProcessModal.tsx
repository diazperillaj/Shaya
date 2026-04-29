// src/features/processes/components/ProcesoDetailModal.tsx
import { X, FlaskConical, Package } from 'lucide-react'
import type { Process, ProcessDetail } from '../models/types'

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmtCOP = (n: number): string =>
  n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })

// ─── Props ───────────────────────────────────────────────────────────────────

interface ProcessDetailModalProps {
  proceso: Process
  detalles: ProcessDetail[]
  /** True while the detalles are still being fetched */
  loading?: boolean
  onClose: () => void
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function ProcessDetailModal({
  proceso,
  detalles,
  loading = false,
  onClose,
}: ProcessDetailModalProps) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">

        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between flex-shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <FlaskConical className="w-5 h-5 flex-shrink-0" />
            Detalle del proceso — Factura {proceso.invoice_number}
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all duration-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* ── Scrollable body ─────────────────────────────────────────────── */}
        <div className="overflow-y-auto flex-1 p-6 space-y-7 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">

          {/* ── Section 1: Datos generales ────────────────────────────────── */}
          <section>
            <SectionTitle label="Datos del proceso" />
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <InfoCard label="Fecha"       value={proceso.process_date} />
              <InfoCard label="No. Factura" value={proceso.invoice_number} />
              <InfoCard label="Caficultor"  value={proceso.parchment_id} />
              <InfoCard
                label="Pergamino (Kg)"
                value={`${proceso.parchment_kg.toFixed(2)} Kg`}
              />
              <InfoCard
                label="Resultante"
                value={`${proceso.resultant_kg.toFixed(2)} Kg`}
              />
              <InfoCard
                label="Rendimiento"
                value={`${proceso.yield_percentage.toFixed(1)} %`}
              />
            </div>

            {proceso.observations && (
              <div className="mt-3 bg-gray-50 border border-gray-100 rounded-xl px-4 py-3 text-sm text-gray-700">
                <span className="font-semibold text-gray-500 block mb-0.5 text-xs uppercase tracking-wide">
                  Observaciones
                </span>
                {proceso.observations}
              </div>
            )}
          </section>

          {/* ── Section 2: Resumen financiero ─────────────────────────────── */}
          <section>
            <SectionTitle label="Resumen financiero" />
            <div className="grid grid-cols-3 gap-3">
              <FinanceCard label="Subtotal" value={fmtCOP(proceso.subtotal)} />
              <FinanceCard label="IVA"      value={fmtCOP(proceso.iva)} />
              <FinanceCard label="Total"    value={fmtCOP(proceso.total)} highlight />
            </div>
          </section>

          {/* ── Section 3: Detalle del proceso ────────────────────────────── */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Package className="w-4 h-4 text-emerald-700" />
              <span className="text-sm font-semibold text-emerald-800 uppercase tracking-wider">
                Detalle del proceso
              </span>
              {detalles.length > 0 && (
                <span className="bg-emerald-800 text-white text-xs font-bold rounded-full px-2 py-0.5">
                  {detalles.length}
                </span>
              )}
            </div>

            {loading && (
              <div className="flex justify-center items-center py-12 text-emerald-700 text-sm gap-2">
                <span className="animate-spin inline-block w-4 h-4 border-2 border-emerald-700 border-t-transparent rounded-full" />
                Cargando detalles…
              </div>
            )}

            {!loading && detalles.length === 0 && (
              <div className="flex flex-col items-center justify-center py-10 border border-dashed border-gray-200 rounded-2xl text-gray-400">
                <Package className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-sm">Sin detalles registrados</p>
              </div>
            )}

            {!loading && detalles.length > 0 && (
              <div className="overflow-x-auto rounded-2xl border border-gray-100 shadow-sm">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-emerald-900 text-white text-xs uppercase tracking-wider">
                      <th className="px-4 py-3 text-left font-semibold">#</th>
                      <th className="px-4 py-3 text-left font-semibold">Producto</th>
                      <th className="px-4 py-3 text-right font-semibold">Bolsas</th>
                      <th className="px-4 py-3 text-right font-semibold">Gramos</th>
                      <th className="px-4 py-3 text-right font-semibold">Valor Unit.</th>
                      <th className="px-4 py-3 text-right font-semibold">IVA</th>
                      <th className="px-4 py-3 text-right font-semibold">Total</th>
                      <th className="px-4 py-3 text-left font-semibold">Observaciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detalles.map((det, i) => (
                      <tr
                        key={det.id}
                        className={`border-t border-gray-100 transition-colors ${
                          i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                        } hover:bg-emerald-50/40`}
                      >
                        <td className="px-4 py-3">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                            {i + 1}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-800">
                          {det.product_id}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {det.bag_quantity}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {det.grams_per_bag} g
                          
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {fmtCOP(det.unit_value)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {fmtCOP(det.iva)}
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-emerald-800">
                          {fmtCOP(det.total)}
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {det.observations ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
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

function InfoCard({ label, value }: { label: string; value: string | number}) {
  return (
    <div className="flex flex-col gap-1 bg-gray-50 border border-gray-100 rounded-xl px-4 py-3">
      <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">
        {label}
      </span>
      <span className="text-sm font-semibold text-gray-800">{value}</span>
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
        className={`text-base font-bold ${
          highlight ? 'text-white' : 'text-emerald-900'
        }`}
      >
        {value}
      </span>
    </div>
  )
}