import { Link } from 'react-router-dom'
import { Warehouse } from 'lucide-react'
import { Card, EmptyState } from '../components/ui'
import { fmtDate, fmtNumber, plural } from '../format'
import { LABOR_INFO } from '../labors/laborConfig'
import type { CycleState, DashboardSummary, FarmRanking } from '../models/types'

const HARVEST_STATUS = {
  waiting: 'Antes de la cosecha',
  open: 'En cosecha',
  harvested: 'Cosechado',
}

/** Estado de los ciclos activos: lo que el caficultor revisa cada día (§3.4) */
export function CyclesTable({ cycles, showFarm }: { cycles: CycleState[]; showFarm: boolean }) {
  return (
    <Card title="Estado de los ciclos">
      {cycles.length === 0 ? (
        <p className="text-sm text-gray-500">No hay ciclos activos.</p>
      ) : (
        <div className="-mx-5 overflow-x-auto px-5">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
                <th className="py-2 pr-3 font-medium">Lote</th>
                <th className="py-2 pr-3 font-medium">Ciclo</th>
                <th className="py-2 pr-3 font-medium">Última labor</th>
                <th className="py-2 pr-3 font-medium">Cosecha</th>
                <th className="py-2 font-medium text-right">Alertas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {cycles.map((cycle) => (
                <tr key={cycle.crop_cycle_id}>
                  <td className="py-2 pr-3">
                    <Link to={`/cultivo/lotes/${cycle.plot_id}`} className="font-medium text-gray-900 hover:text-emerald-800">
                      {cycle.plot_name}
                    </Link>
                    {showFarm && <span className="block text-xs text-gray-400">{cycle.farm_name}</span>}
                  </td>
                  <td className="py-2 pr-3 text-gray-600">
                    Ciclo {cycle.cycle_number}
                    <span className="block text-xs text-gray-400">{plural(cycle.days, 'día', 'días')}</span>
                  </td>
                  <td className="py-2 pr-3 text-gray-600">
                    {cycle.last_labor ? (
                      <>
                        {LABOR_INFO[cycle.last_labor.kind]?.label ?? cycle.last_labor.kind}
                        <span className="block text-xs text-gray-400">{fmtDate(cycle.last_labor.date)}</span>
                      </>
                    ) : (
                      <span className="text-gray-400">Sin labores</span>
                    )}
                  </td>
                  <td className="py-2 pr-3 text-gray-600">
                    {HARVEST_STATUS[cycle.harvest_status]}
                    {cycle.harvest_status === 'waiting' && (
                      <span className="block text-xs text-gray-400">
                        {cycle.estimated_harvest
                          ? `Estimada: ${fmtDate(cycle.estimated_harvest)} (±14 días)`
                          : 'Registra la floración para estimarla'}
                      </span>
                    )}
                  </td>
                  <td className="py-2 text-right">
                    {cycle.alerts > 0 ? (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">{cycle.alerts}</span>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

const healthTone = (value: number | null, threshold: number | null) => {
  if (value === null) return 'text-gray-300'
  if (threshold !== null && value >= threshold) return 'bg-red-50 text-red-700'
  return 'bg-emerald-50 text-emerald-800'
}

/** Ranking de fincas y mapa de sanidad (§3.5) */
export function FarmRankingTable({ rows, onSelect }: { rows: FarmRanking[]; onSelect: (farmId: number) => void }) {
  const ranked = [...rows].sort((a, b) => (b.yield_pct ?? -1) - (a.yield_pct ?? -1))
  return (
    <Card title="Fincas: producción, calidad y sanidad">
      <div className="-mx-5 overflow-x-auto px-5">
        <table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
              <th className="py-2 pr-3 font-medium">Finca</th>
              <th className="py-2 pr-3 text-right font-medium">Pergamino</th>
              <th className="py-2 pr-3 text-right font-medium">Rendimiento</th>
              <th className="py-2 pr-3 text-right font-medium">Puntaje</th>
              <th className="py-2 pr-3 text-center font-medium">Broca</th>
              <th className="py-2 pr-3 text-center font-medium">Roya</th>
              <th className="py-2 text-right font-medium">Alertas</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {ranked.map((row) => (
              <tr key={row.farm_id}>
                <td className="py-2 pr-3">
                  <button
                    type="button"
                    onClick={() => onSelect(row.farm_id)}
                    className="text-left font-medium text-gray-900 hover:text-emerald-800"
                  >
                    {row.farm_name}
                  </button>
                  <span className="block text-xs text-gray-400">{plural(row.plots_active, 'lote', 'lotes')}</span>
                </td>
                <td className="py-2 pr-3 text-right text-gray-600">{fmtNumber(row.parchment_kg, 0, 'kg')}</td>
                <td className="py-2 pr-3 text-right text-gray-600">
                  {row.yield_pct === null ? '—' : `${fmtNumber(row.yield_pct, 1)} %`}
                </td>
                <td className="py-2 pr-3 text-right text-gray-600">{row.score_avg === null ? '—' : fmtNumber(row.score_avg, 1)}</td>
                <td className="py-2 pr-3 text-center">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${healthTone(row.broca_pct, row.broca_threshold)}`}>
                    {row.broca_pct === null ? '—' : `${fmtNumber(row.broca_pct, 1)} %`}
                  </span>
                </td>
                <td className="py-2 pr-3 text-center text-xs text-gray-600">
                  {row.roya_pct === null ? '—' : `${fmtNumber(row.roya_pct, 1)} %`}
                </td>
                <td className="py-2 text-right text-xs">
                  <span className="text-red-700">{row.alerts_high}</span>
                  <span className="text-gray-300"> · </span>
                  <span className="text-amber-700">{row.alerts_medium}</span>
                  <span className="text-gray-300"> · </span>
                  <span className="text-sky-700">{row.alerts_info}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-gray-400">
        Broca y roya: el mayor de los últimos muestreos de sus lotes; en rojo, sobre el umbral de la finca. Alertas: riesgos ·
        desvíos · recordatorios.
      </p>
    </Card>
  )
}

/** Café guardado en finca, por entrar al inventario (§3.5) */
export function StoredCoffee({ summary }: { summary: DashboardSummary }) {
  return (
    <Card title="Café guardado en finca">
      {summary.stored_dryings.length === 0 ? (
        <EmptyState icon={Warehouse} title="No hay pergamino guardado" description="Todo el café cerrado ya salió de las fincas." />
      ) : (
        <ul className="grid grid-cols-1 gap-x-8 text-sm md:grid-cols-2">
          {summary.stored_dryings.map((drying) => (
            <li key={drying.drying_id} className="flex items-center justify-between gap-3 border-b border-gray-50 py-2">
              <Link to={`/cultivo/secados/${drying.drying_id}`} className="min-w-0 hover:text-emerald-800">
                <span className="font-medium text-gray-900">Secado {drying.drying_id}</span>
                <span className="block truncate text-xs text-gray-400">
                  {drying.farm_name} · cerrado el {fmtDate(drying.end_date)} · hace {plural(drying.days, 'día', 'días')}
                </span>
              </Link>
              <span className="whitespace-nowrap text-gray-600">{fmtNumber(drying.output_kg, 1, 'kg')}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
