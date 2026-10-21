import { CalendarDays, MessageSquareText, Mountain, User } from 'lucide-react'
import { fmtCOP } from '../../../components/charts/chartData'
import { BusyOverlay } from '../../../components/ui/Busy'
import { bags, fmtDate, fmtUnits, type StockLot } from '../models/inventory'

/** Un lote con existencias: su origen y lo que queda de cada producto */
export default function LotCard({ lot }: { lot: StockLot }) {
  const origin = [lot.farmer_name, lot.farm_name].filter(Boolean).join(' · ')

  return (
    <article className="relative flex flex-col rounded-2xl border border-gray-100 bg-white shadow-sm">
      <header className="px-5 pb-4 pt-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
              Lote #{lot.id} · Factura {lot.invoice_number}
            </p>
            <h3 className="mt-1 truncate text-lg font-semibold text-gray-900">{lot.variety || 'Sin variedad'}</h3>
          </div>
          <span
            title="Días desde el proceso"
            className="shrink-0 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium tabular-nums text-gray-600"
          >
            {lot.ageDays} {lot.ageDays === 1 ? 'día' : 'días'}
          </span>
        </div>

        <div className="mt-3 flex flex-col gap-1.5 text-sm text-gray-600">
          <p className="flex items-center gap-2">
            <User className="h-4 w-4 shrink-0 text-gray-400" aria-hidden />
            <span className="truncate">{origin || 'Sin caficultor'}</span>
          </p>
          <p className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4 shrink-0 text-gray-400" aria-hidden />
            <span className="truncate">Procesado el {fmtDate(lot.process_date)}</span>
          </p>
          {lot.altitude !== null && lot.altitude > 0 && (
            <p className="flex items-center gap-2">
              <Mountain className="h-4 w-4 shrink-0 text-gray-400" aria-hidden />
              <span className="truncate">{fmtUnits(lot.altitude)} msnm</span>
            </p>
          )}
          {lot.observations && (
            <p className="flex items-start gap-2 text-gray-500">
              <MessageSquareText className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" aria-hidden />
              <span className="line-clamp-2">{lot.observations}</span>
            </p>
          )}
        </div>
      </header>

      <ul className="flex flex-col gap-3 border-t border-gray-100 px-5 py-4" aria-label={`Productos disponibles del lote ${lot.id}`}>
        {lot.available.map((product) => {
          const share = product.total_in > 0 ? Math.min(1, product.remaining_quantity / product.total_in) : 1
          return (
            <li key={product.detail_id}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="truncate text-gray-700">{product.name}</span>
                <span className="shrink-0 tabular-nums">
                  <span className="font-semibold text-gray-900">{fmtUnits(product.remaining_quantity)}</span>
                  <span className="text-gray-400"> de {fmtUnits(product.total_in)}</span>
                </span>
              </div>
              <div aria-hidden className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-gray-100">
                <div className="h-full rounded-full bg-emerald-600" style={{ width: `${share * 100}%` }} />
              </div>
            </li>
          )
        })}
      </ul>

      <footer className="mt-auto flex items-center justify-between gap-3 rounded-b-2xl border-t border-gray-100 bg-gray-50 px-5 py-3 text-sm">
        <span className="text-gray-600">
          <span className="font-semibold text-gray-900">{bags(lot.remaining)}</span> disponibles
        </span>
        <span className="tabular-nums text-gray-500" title="Valor a costo de producción">
          {lot.value !== null ? fmtCOP(lot.value) : 'Sin costo'}
        </span>
      </footer>
      <BusyOverlay />
    </article>
  )
}
