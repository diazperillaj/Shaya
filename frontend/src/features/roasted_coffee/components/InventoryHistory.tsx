import { useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import DataTable from '../../../components/ui/DataTable'
import { EventColumns, eventLabel, LotHistoryColumns, toLotHistoryRows } from '../models/columns'
import { fmtShortDate } from '../models/inventory'
import type { InventoryDashboard } from '../models/types'

const TABS = [
  { id: 'lots', label: 'Lotes y productos' },
  { id: 'events', label: 'Entradas y salidas' },
] as const

type Tab = (typeof TABS)[number]['id']

const includes = (texts: (string | number | null)[], query: string) =>
  texts.some((text) => String(text ?? '').toLowerCase().includes(query))

/** Todo lo que ha pasado por el inventario, incluidos los lotes agotados */
export default function InventoryHistory({ data }: { data: InventoryDashboard }) {
  const [tab, setTab] = useState<Tab>('lots')
  const [search, setSearch] = useState('')
  const query = search.trim().toLowerCase()

  const lotRows = useMemo(() => toLotHistoryRows(data.lots), [data.lots])
  // Lo más reciente primero
  const events = useMemo(() => [...data.events].reverse(), [data.events])

  const filteredLots = lotRows.filter((row) =>
    includes([`#${row.lot_id}`, row.invoice_number, row.variety, row.farmer, row.product_name, fmtShortDate(row.process_date)], query),
  )
  const filteredEvents = events.filter((e) =>
    includes([`#${e.lot_id}`, e.product_name, eventLabel(e), e.reference, e.note, fmtShortDate(e.event_date)], query),
  )

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div role="tablist" aria-label="Histórico" className="inline-flex self-start rounded-xl bg-gray-100 p-1 text-sm font-medium">
          {TABS.map((t) => {
            const active = t.id === tab
            const count = t.id === 'lots' ? filteredLots.length : filteredEvents.length
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={active}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 transition-colors duration-150 ${
                  active ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t.label}
                <span className="tabular-nums text-xs text-gray-400">{count}</span>
              </button>
            )
          })}
        </div>

        <div className="relative w-full sm:max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={tab === 'lots' ? 'Buscar lote, variedad, caficultor…' : 'Buscar producto, venta, feria…'}
            aria-label="Buscar en el histórico"
            className="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600/25"
          />
        </div>
      </div>

      {tab === 'lots' ? (
        <DataTable
          key="lots"
          columns={LotHistoryColumns}
          data={filteredLots}
          isAdmin={false}
          initialPageSize={20}
          emptyMessage="Ningún lote coincide con la búsqueda"
        />
      ) : (
        <DataTable
          key="events"
          columns={EventColumns}
          data={filteredEvents}
          isAdmin={false}
          initialPageSize={20}
          emptyMessage="Ningún movimiento coincide con la búsqueda"
        />
      )}
    </div>
  )
}
