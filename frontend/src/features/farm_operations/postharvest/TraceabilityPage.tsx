import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { GitBranch } from 'lucide-react'
import { Badge, Card, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtDateTime, fmtMoney, fmtNumber } from '../format'
import { LABOR_INFO } from '../labors/laborConfig'
import { DRYING_DESTINATION_LABELS } from '../models/labels'
import type { DryingTrace } from '../models/types'
import { fetchDryingTrace, fetchParchmentTrace } from '../services/postharvest.api'
import CompositionBars from './CompositionBars'
import { dryingMethodName } from './describe'

/**
 * Trazabilidad de un secado, o del pergamino del inventario que produjo:
 * de qué lotes viene el café, en qué proporción, de qué ciclos y pasadas, y
 * qué labores tuvo cada ciclo.
 */
export function DryingTracePage() {
  const { dryingId } = useParams()
  const load = useCallback(() => fetchDryingTrace(Number(dryingId)), [dryingId])
  return <TraceView load={load} />
}

export function ParchmentTracePage() {
  const { parchmentId } = useParams()
  const load = useCallback(() => fetchParchmentTrace(Number(parchmentId)), [parchmentId])
  return <TraceView load={load} />
}

function TraceView({ load }: { load: () => Promise<DryingTrace> }) {
  const { data: trace, error } = useLoader(load)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link to="/cultivo/fincas" className="text-sm text-emerald-800 hover:underline">← Volver a las fincas</Link>
        <ErrorMessage message={error} />
      </div>
    )
  }
  if (!trace) return <Loading />

  const { drying } = trace
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={GitBranch}
        back={{ to: `/cultivo/secados/${drying.id}`, label: `Secado ${drying.id}` }}
        title="Trazabilidad"
        subtitle={
          <>
            {drying.farm_name} · {dryingMethodName(drying)}
            {drying.output_kg !== null && <> · {fmtNumber(drying.output_kg, 1, 'kg')} de pergamino seco</>}
            {drying.yield_pct !== null && <> · rendimiento {fmtNumber(drying.yield_pct, 1)} %</>}
            {drying.destination && <> · {DRYING_DESTINATION_LABELS[drying.destination]}</>}
            {drying.parchment_id !== null && <> (pergamino n.º {drying.parchment_id})</>}
          </>
        }
      />

      <Card title="De qué lotes viene">
        <CompositionBars plots={trace.plots} />
        <p className="mt-3 text-xs text-gray-400">
          Proporción del café cereza de cada lote: {fmtNumber(drying.cherry_kg_traced, 1, 'kg')} en total.
        </p>
      </Card>

      {trace.plots.map((plot) => (
        <Card key={plot.plot_id} title={`${plot.plot_name} · ${plot.variety} · ${fmtNumber(plot.share_pct, 1)} %`}>
          <div className="flex flex-col gap-5">
            {plot.cycles.map((cycle) => (
              <section key={cycle.crop_cycle_id} className="flex flex-col gap-3">
                <p className="flex flex-wrap items-center gap-2 text-sm font-medium text-gray-900">
                  Ciclo {cycle.cycle_number}
                  <Badge tone={cycle.status === 'active' ? 'green' : 'gray'}>{cycle.status === 'active' ? 'Activo' : 'Cerrado'}</Badge>
                  <span className="font-normal text-gray-500">
                    {fmtDate(cycle.start_date)} – {cycle.end_date ? fmtDate(cycle.end_date) : 'en curso'}
                  </span>
                </p>
                <p className="text-sm text-gray-600">
                  Cosechas:{' '}
                  {cycle.harvests.map((harvest, index) => (
                    <span key={harvest.harvest_id}>
                      {index > 0 && ', '}
                      <Link to={`/cultivo/cosechas/${harvest.harvest_id}`} className="text-emerald-800 hover:underline">
                        pasada {harvest.pass_number}
                      </Link>{' '}
                      ({fmtNumber(harvest.cherry_kg, 1, 'kg')})
                    </span>
                  ))}
                </p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
                  {cycle.labors.map((labor) => {
                    const { icon: Icon, plural } = LABOR_INFO[labor.kind]
                    return (
                      <div key={labor.kind} className="rounded-xl border border-gray-100 px-3 py-2">
                        <p className="flex items-center gap-1.5 text-xs text-gray-500"><Icon className="h-3.5 w-3.5" /> {plural}</p>
                        <p className="text-base font-semibold text-gray-900">{labor.count}</p>
                        <p className="text-xs text-gray-400">
                          {labor.last_date ? `Última: ${fmtDate(labor.last_date)}` : 'Sin registros'}
                          {labor.total_cost ? ` · ${fmtMoney(labor.total_cost)}` : ''}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </section>
            ))}
            <Link to={`/cultivo/lotes/${plot.plot_id}`} className="w-fit text-sm font-medium text-emerald-800 hover:underline">
              Ver el lote y sus labores →
            </Link>
          </div>
        </Card>
      ))}

      <Card title="Beneficios">
        <ul className="divide-y divide-gray-100">
          {trace.wet_processings.map((wet) => (
            <li key={wet.wet_processing_id} className="flex flex-wrap items-center justify-between gap-3 py-2 text-sm">
              <Link to={`/cultivo/beneficios/${wet.wet_processing_id}`} className="text-gray-900 hover:text-emerald-800">
                Beneficio {wet.wet_processing_id}
                {wet.pulped_at && <span className="text-gray-500"> · {fmtDateTime(wet.pulped_at)}</span>}
              </Link>
              <span className="text-gray-600">
                {fmtNumber(wet.cherry_kg, 1, 'kg')} cereza → {fmtNumber(wet.washed_kg, 1, 'kg')} lavado · aportó{' '}
                {fmtNumber(wet.wet_kg, 1, 'kg')} a este secado
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
