import { Link } from 'react-router-dom'
import { Card } from '../components/ui'
import type { QualityProjection } from '../models/types'
import {
  YIELD_FACTOR_HINT,
  fmtCompleteness,
  fmtDefects,
  fmtScore,
  fmtYieldFactor,
} from './projectionInfo'

/** Proyección de calidad de cada ciclo activo, en el dashboard (dashboards-alertas §3.4) */
export default function ProjectionsTable({
  projections,
  showFarm,
}: {
  projections: QualityProjection[]
  showFarm: boolean
}) {
  return (
    <Card title="Proyección de calidad">
      {projections.length === 0 ? (
        <p className="text-sm text-gray-500">No hay ciclos activos para proyectar.</p>
      ) : (
        <>
          <div className="-mx-5 overflow-x-auto px-5">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
                  <th className="py-2 pr-3 font-medium">Lote</th>
                  <th className="py-2 pr-3 font-medium text-right">Puntaje</th>
                  <th className="py-2 pr-3 font-medium text-right">Defectos</th>
                  <th className="py-2 pr-3 font-medium text-right" title={YIELD_FACTOR_HINT}>Factor</th>
                  <th className="py-2 font-medium text-right">Datos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {projections.map((p) => (
                  <tr key={p.crop_cycle_id}>
                    <td className="py-2 pr-3">
                      <Link to={`/cultivo/lotes/${p.plot_id}`} className="font-medium text-gray-900 hover:text-emerald-800">
                        {p.plot_name}
                      </Link>
                      <span className="block text-xs text-gray-400">
                        {showFarm ? `${p.farm_name} · ciclo ${p.cycle_number}` : `Ciclo ${p.cycle_number}`}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-right font-medium text-gray-900">{fmtScore(p)}</td>
                    <td className="py-2 pr-3 text-right text-gray-600">{fmtDefects(p)}</td>
                    <td className="py-2 pr-3 text-right text-gray-600">{fmtYieldFactor(p)}</td>
                    <td className="py-2 text-right text-gray-600">{fmtCompleteness(p)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-gray-400">
            {projections[0].disclaimer} Los datos que aún no existen (cosecha, beneficio, secado) se proyectan con los
            valores típicos de cada finca.
          </p>
        </>
      )}
    </Card>
  )
}
