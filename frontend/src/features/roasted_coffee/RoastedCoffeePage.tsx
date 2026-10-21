// src/features/roasted_coffee/RoastedCoffeePage.tsx
import { useMemo, useState } from 'react'
import { AlertCircle, ArrowLeft, Coffee, History, PackageOpen, RefreshCw, Search } from 'lucide-react'

import { CardSkeleton, ChartSkeleton, KpiSkeletonGrid } from '../../components/ui/Busy'
import { BusyScope, useMinDuration } from '../../components/ui/busyContext'
import InventoryCharts from './components/InventoryCharts'
import InventoryHistory from './components/InventoryHistory'
import InventoryKpiGrid, { KPI_GRID } from './components/InventoryKpiGrid'
import LotCard from './components/LotCard'
import { useInventoryDashboard } from './hooks/useInventoryDashboard'
import { bags, inventoryKpis, matchesLot, stockLots } from './models/inventory'

const PRIMARY_BUTTON =
  'flex items-center gap-2 rounded-xl bg-emerald-900 px-4 py-2.5 text-sm font-medium text-white shadow-md transition duration-150 ease-out hover:bg-emerald-950 hover:shadow-lg active:scale-[0.97]'
const SECONDARY_BUTTON =
  'flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm text-gray-700 shadow-sm transition duration-150 ease-out hover:bg-gray-50 hover:shadow-md active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100'

type View = 'dashboard' | 'history'

export default function RoastedCoffeePage() {
  const { data, loading, error, refresh } = useInventoryDashboard()
  const [view, setView] = useState<View>('dashboard')
  const [search, setSearch] = useState('')

  // Las antigüedades se cuentan hasta hoy; cambia solo al cambiar de día
  const dayKey = new Date().toDateString()
  const today = useMemo(() => new Date(dayKey), [dayKey])

  const stock = useMemo(() => (data ? stockLots(data.lots, today) : []), [data, today])
  const kpis = useMemo(
    () => (data ? inventoryKpis(data.lots, stock, data.events, today) : null),
    [data, stock, today],
  )
  const visibleLots = stock.filter((lot) => matchesLot(lot, search))

  // Al actualizar, las cifras siguen a la vista mientras llegan las nuevas
  const refreshing = loading && data !== null
  const spinning = useMinDuration(loading)

  if (error && !data) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4 text-red-600">
        <AlertCircle className="h-10 w-10" />
        <p className="text-sm font-medium">{error}</p>
        <button onClick={refresh} className={PRIMARY_BUTTON}>
          <RefreshCw className="h-4 w-4" /> Reintentar
        </button>
      </div>
    )
  }

  const subtitle = !data
    ? 'Cargando inventario…'
    : view === 'history'
      ? `${data.lots.length} ${data.lots.length === 1 ? 'lote' : 'lotes'} · ${data.events.length} entradas y salidas registradas`
      : `${bags(kpis?.available ?? 0)} disponibles en ${stock.length} ${stock.length === 1 ? 'lote' : 'lotes'}`

  return (
    <div className="flex flex-col gap-6 text-left">
      {/* ── Encabezado ───────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-emerald-100 p-2.5">
            <Coffee className="h-6 w-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {view === 'history' ? 'Histórico del maquilado' : 'Maquilado'}
            </h1>
            <p className="text-sm text-gray-400">{subtitle}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {view === 'dashboard' ? (
            <button type="button" onClick={() => setView('history')} className={PRIMARY_BUTTON}>
              <History className="h-4 w-4" /> Histórico
            </button>
          ) : (
            <button type="button" onClick={() => setView('dashboard')} className={PRIMARY_BUTTON}>
              <ArrowLeft className="h-4 w-4" /> Volver al tablero
            </button>
          )}
          <button
            type="button"
            onClick={refresh}
            disabled={spinning}
            aria-busy={spinning || undefined}
            className={SECONDARY_BUTTON}
          >
            <RefreshCw className={`h-4 w-4 ${spinning ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {error && (
        <p className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </p>
      )}

      <BusyScope busy={refreshing}>
        {view === 'history' ? (
          data ? <InventoryHistory data={data} /> : <CardSkeleton rows={8} label="Cargando histórico…" />
        ) : (
          <>
            {kpis ? <InventoryKpiGrid kpis={kpis} /> : <KpiSkeletonGrid count={6} className={KPI_GRID} />}

            {/* ── Inventario actual, por lote ──────────────────────────────── */}
            <section aria-labelledby="stock-title" className="flex flex-col gap-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 id="stock-title" className="text-lg font-semibold text-gray-900">Inventario actual</h2>
                  <p className="text-sm text-gray-400">Lotes con bolsas disponibles; los agotados quedan en el histórico</p>
                </div>
                {stock.length > 0 && (
                  <div className="relative w-full sm:max-w-xs">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      placeholder="Buscar lote, variedad, caficultor…"
                      aria-label="Buscar lote"
                      className="w-full rounded-xl border border-gray-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600/25"
                    />
                  </div>
                )}
              </div>

              {!data ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                  <CardSkeleton rows={4} label="Cargando lotes…" />
                  <CardSkeleton rows={4} label="Cargando lotes…" />
                  <CardSkeleton rows={4} label="Cargando lotes…" />
                </div>
              ) : stock.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-12 text-center">
                  <PackageOpen className="mx-auto h-8 w-8 text-gray-300" aria-hidden />
                  <p className="mt-3 text-sm font-medium text-gray-700">No hay café maquilado disponible</p>
                  <p className="mt-1 text-sm text-gray-400">
                    Los lotes aparecen aquí al registrar un proceso. Los agotados quedan en el histórico.
                  </p>
                  <button type="button" onClick={() => setView('history')} className={`${SECONDARY_BUTTON} mx-auto mt-5`}>
                    <History className="h-4 w-4" /> Ver histórico
                  </button>
                </div>
              ) : visibleLots.length === 0 ? (
                <p className="rounded-2xl border border-gray-100 bg-white px-6 py-10 text-center text-sm text-gray-400">
                  Ningún lote disponible coincide con «{search.trim()}»
                </p>
              ) : (
                <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {visibleLots.map((lot) => (
                    <LotCard key={lot.id} lot={lot} />
                  ))}
                </div>
              )}
            </section>

            {/* ── Análisis ─────────────────────────────────────────────────── */}
            <section aria-labelledby="analysis-title" className="flex flex-col gap-4">
              <div>
                <h2 id="analysis-title" className="text-lg font-semibold text-gray-900">Análisis</h2>
                <p className="text-sm text-gray-400">Cómo ha entrado y salido el café de la bodega</p>
              </div>
              {data ? (
                <InventoryCharts stock={stock} events={data.events} today={today} />
              ) : (
                <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                  <div className="xl:col-span-2">
                    <ChartSkeleton height={280} />
                  </div>
                  <ChartSkeleton />
                  <ChartSkeleton />
                </div>
              )}
            </section>
          </>
        )}
      </BusyScope>
    </div>
  )
}
