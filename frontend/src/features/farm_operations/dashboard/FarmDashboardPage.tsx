import { useCallback, useMemo, useState } from 'react'
import { BarChart3, ChevronDown, LayoutDashboard, RefreshCw } from 'lucide-react'
import GlobalChartDefs from '../../../components/charts/GlobalChartDefs'
import { useAuth } from '../../auth/AuthContext'
import { Button, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { todayIso } from '../format'
import ProjectionsTable from '../projection/ProjectionsTable'
import {
  fetchCycleStates,
  fetchDashboardAlerts,
  fetchDashboardSummary,
  fetchFarmRanking,
  fetchProductionCharts,
  fetchQualityCharts,
  fetchQualityProjections,
  fetchSeasons,
} from '../services/dashboard.api'
import { fetchFarms } from '../services/farms.api'
import { AlertsPanel, RemindersCard } from './AlertsPanel'
import { ProductionSection, QualitySection } from './ChartSections'
import PeriodPicker from './PeriodPicker'
import { loadChoice, resolvePreset, saveChoice, type PeriodChoice } from './period'
import { CyclesTable, FarmRankingTable, StoredCoffee } from './RoleTables'
import SummaryCards from './SummaryCards'

const wideScreen = () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches

function initialChoice(today: string): PeriodChoice {
  const saved = loadChoice()
  if (saved?.preset === 'custom') return saved
  const preset = saved?.preset ?? 'year'
  // Los de cosecha se resuelven al llegar las temporadas; mientras, el último año
  return { preset, ...(resolvePreset(preset, [], today) ?? resolvePreset('year', [], today)!) }
}

/**
 * Dashboard del cultivo (dashboards-alertas): la pantalla de inicio del
 * caficultor y la entrada del administrador al módulo. Mismo dashboard para
 * ambos; cambia el alcance (el administrador elige una finca o todas).
 */
export default function FarmDashboardPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const today = todayIso()
  const [farmId, setFarmId] = useState<number | null>(null)
  const [choice, setChoice] = useState<PeriodChoice>(() => initialChoice(today))
  const [chartsOpen, setChartsOpen] = useState(wideScreen)

  const { data: farms } = useLoader(useCallback(() => fetchFarms(), []))
  const { data: seasons } = useLoader(useCallback(() => fetchSeasons(farmId), [farmId]))

  // Los botones de cosecha dependen de las temporadas del alcance elegido: se resuelven al vuelo
  const period = useMemo<PeriodChoice>(() => {
    if (choice.preset === 'custom') return choice
    return { preset: choice.preset, ...(resolvePreset(choice.preset, seasons ?? [], today) ?? choice) }
  }, [choice, seasons, today])

  const changePeriod = (next: PeriodChoice) => {
    setChoice(next)
    saveChoice(next)
  }

  const scope = useMemo(() => ({ farmId, from: period.from, to: period.to }), [farmId, period.from, period.to])
  const state = useLoader(
    useCallback(() => Promise.all([fetchDashboardSummary(scope), fetchDashboardAlerts(scope.farmId)]), [scope]),
  )
  const charts = useLoader(
    useCallback(() => Promise.all([fetchProductionCharts(scope), fetchQualityCharts(scope)]), [scope]),
  )
  const showCycles = !isAdmin || farmId !== null
  const cycles = useLoader(useCallback(() => (showCycles ? fetchCycleStates(farmId) : Promise.resolve([])), [showCycles, farmId]))
  // Por separado: si el modelo no está disponible, el resto del dashboard sigue
  const projections = useLoader(
    useCallback(() => (showCycles ? fetchQualityProjections(farmId) : Promise.resolve([])), [showCycles, farmId]),
  )
  const showRanking = isAdmin && farmId === null
  const ranking = useLoader(
    useCallback(() => (showRanking ? fetchFarmRanking(scope.from, scope.to) : Promise.resolve([])), [showRanking, scope]),
  )

  const multiFarm = (farms?.length ?? 0) > 1
  const showFarm = multiFarm && farmId === null
  const [summary, alerts] = state.data ?? [null, []]
  const refresh = () => {
    state.reload()
    charts.reload()
    cycles.reload()
    projections.reload()
    ranking.reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <GlobalChartDefs />
      <PageHeader
        icon={LayoutDashboard}
        title="Resumen del cultivo"
        subtitle={
          farmId !== null
            ? farms?.find((farm) => farm.id === farmId)?.name
            : isAdmin ? 'Todas las fincas' : multiFarm ? 'Tus fincas' : farms?.[0]?.name
        }
        actions={
          <>
            {multiFarm && (
              <select
                value={farmId ?? ''}
                onChange={(e) => setFarmId(e.target.value ? Number(e.target.value) : null)}
                className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 shadow-sm"
                aria-label="Finca"
              >
                <option value="">Todas las fincas</option>
                {farms?.map((farm) => (
                  <option key={farm.id} value={farm.id}>{farm.name}</option>
                ))}
              </select>
            )}
            <Button icon={RefreshCw} onClick={refresh}>Actualizar</Button>
          </>
        }
      />

      <PeriodPicker value={period} seasons={seasons ?? []} today={today} onChange={changePeriod} />

      {state.error && <ErrorMessage message={state.error} />}
      {summary ? (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <SummaryCards summary={summary} alerts={alerts} />
          </div>
          <div className="order-first flex flex-col gap-6 xl:order-none">
            <AlertsPanel alerts={alerts} showFarm={showFarm} />
            <RemindersCard alerts={alerts} showFarm={showFarm} />
          </div>
        </div>
      ) : (
        !state.error && <Loading />
      )}

      {showCycles && cycles.data && <CyclesTable cycles={cycles.data} showFarm={showFarm} />}
      {showCycles && projections.error && <ErrorMessage message={projections.error} />}
      {showCycles && projections.data && <ProjectionsTable projections={projections.data} showFarm={showFarm} />}
      {showRanking && ranking.data && <FarmRankingTable rows={ranking.data} onSelect={setFarmId} />}
      {isAdmin && summary && <StoredCoffee summary={summary} />}

      <section className="flex flex-col gap-4">
        <button
          type="button"
          onClick={() => setChartsOpen(!chartsOpen)}
          className="flex w-fit items-center gap-2 text-sm font-semibold text-gray-800"
          aria-expanded={chartsOpen}
        >
          <BarChart3 className="h-4 w-4 text-emerald-800" />
          Gráficas del periodo
          <ChevronDown className={`h-4 w-4 transition ${chartsOpen ? 'rotate-180' : ''}`} />
        </button>
        {chartsOpen && (
          <>
            {charts.error && <ErrorMessage message={charts.error} />}
            {charts.data ? (
              <>
                <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Producción</h2>
                <ProductionSection charts={charts.data[0]} />
                <h2 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Calidad y sanidad</h2>
                <QualitySection charts={charts.data[1]} />
              </>
            ) : (
              !charts.error && <Loading />
            )}
          </>
        )}
      </section>
    </div>
  )
}
