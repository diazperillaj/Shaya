import { useCallback } from 'react'
import { Check, RefreshCw } from 'lucide-react'
import { Skeleton } from '../../../components/ui/Busy'
import { Button, Card, ErrorMessage } from '../components/ui'
import { useLoader } from '../components/useLoader'
import type { QualityProjection } from '../models/types'
import { fetchQualityProjection } from '../services/plots.api'
import {
  STAGES,
  YIELD_FACTOR_HINT,
  fmtCompleteness,
  fmtDefects,
  fmtScore,
  fmtYieldFactor,
} from './projectionInfo'

/**
 * Calidad esperada del ciclo activo del lote. Se monta con la clave del
 * ciclo: al abrir o cerrar un ciclo, vuelve a proyectar.
 */
export default function QualityProjectionCard({ plotId }: { plotId: number }) {
  const { data, error, loading, refreshing, reload } = useLoader(
    useCallback(() => fetchQualityProjection(plotId), [plotId]),
  )

  return (
    <Card
      title="Proyección de calidad"
      busy={refreshing}
      actions={<Button icon={RefreshCw} onClick={reload} loading={loading}>Recalcular</Button>}
    >
      {error ? <ErrorMessage message={error} /> : data ? <ProjectionBody projection={data} /> : <ProjectionSkeleton />}
    </Card>
  )
}

/** Las tres cifras y la barra de datos, vacías, mientras el modelo proyecta */
function ProjectionSkeleton() {
  return (
    <div role="status" className="flex flex-col gap-4">
      <span className="sr-only">Calculando la proyección…</span>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex flex-col gap-2 rounded-xl bg-gray-50 px-4 py-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-6 w-16" />
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex justify-between">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-3 w-10" />
        </div>
        <Skeleton className="h-1.5 w-full rounded-full" />
        <div className="flex flex-wrap gap-2">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-5 w-20 rounded-full" />
          ))}
        </div>
      </div>
    </div>
  )
}

function ProjectionBody({ projection: p }: { projection: QualityProjection }) {
  return (
    <div className="flex flex-col gap-4 text-left">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Metric label="Puntaje SCA" value={fmtScore(p)} />
        <Metric label="Defectos" value={fmtDefects(p)} />
        <Metric label="Factor de rendimiento" value={fmtYieldFactor(p)} hint={YIELD_FACTOR_HINT} />
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Datos del ciclo registrados</span>
          <span className="font-medium text-gray-700">{fmtCompleteness(p)}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-gray-100">
          <div className="h-full rounded-full bg-emerald-600" style={{ width: `${Math.round(p.completeness * 100)}%` }} />
        </div>
        <ul className="flex flex-wrap gap-2">
          {STAGES.map((stage) => {
            const done = p.stages.includes(stage.id)
            return (
              <li
                key={stage.id}
                className={`flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs ${
                  done ? 'bg-emerald-50 text-emerald-800' : 'bg-gray-50 text-gray-400'
                }`}
              >
                {done && <Check className="h-3 w-3" />}
                {stage.label}
              </li>
            )
          })}
        </ul>
        {p.stages.length < STAGES.length && (
          <p className="text-xs text-gray-500">Las etapas que faltan se proyectan con los valores típicos de la finca.</p>
        )}
      </div>

      <p className="text-xs text-gray-400">
        {p.disclaimer} Modelo {p.model_version}.
      </p>
    </div>
  )
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl bg-gray-50 px-4 py-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-gray-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
    </div>
  )
}
