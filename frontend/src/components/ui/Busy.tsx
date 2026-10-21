import { useContext, type CSSProperties } from 'react'
import { BusyContext, useMinDuration } from './busyContext'

/**
 * Estados de carga compartidos.
 *
 * - Primera carga: esqueletos con la forma de lo que viene (`Skeleton`,
 *   `CardSkeleton`, `KpiSkeletonGrid`, `ChartSkeleton`), así la página no
 *   se ve vacía mientras llegan los datos.
 * - Actualizar: los datos siguen a la vista y cada tarjeta muestra una barra
 *   de progreso y un velo (`BusyOverlay`). Las tarjetas lo leen de
 *   `BusyScope` (busyContext.ts), sin pasar la prop por cada componente.
 */

const OVERLAY_TONES = {
  // La barra toma el color del texto: en modo oscuro los fondos se invierten y los textos siguen claros
  light: { veil: 'bg-white/60', track: 'bg-emerald-100', bar: 'text-emerald-600' },
  /** Sobre las tarjetas verde oscuro (KPI destacado) */
  accent: { veil: 'bg-emerald-900/60', track: 'bg-emerald-800', bar: 'text-emerald-300' },
}

/**
 * Barra de progreso y velo sobre una tarjeta que se está actualizando. Va
 * como último hijo de un contenedor `relative`; sigue su borde redondeado.
 */
export function BusyOverlay({ busy, tone = 'light' }: { busy?: boolean; tone?: keyof typeof OVERLAY_TONES }) {
  const scoped = useContext(BusyContext)
  const visible = useMinDuration(busy ?? scoped)
  if (!visible) return null
  const colors = OVERLAY_TONES[tone]
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 animate-fadeIn overflow-hidden rounded-[inherit]">
      <div className={`absolute inset-0 ${colors.veil}`} />
      <div className={`absolute inset-x-0 top-0 h-[3px] overflow-hidden ${colors.track}`}>
        <div className={`h-full w-1/3 animate-progress rounded-full bg-current ${colors.bar}`} />
      </div>
    </div>
  )
}

/** Bloque gris que late en lugar de un texto o número que aún no llega */
export function Skeleton({ className = '', style }: { className?: string; style?: CSSProperties }) {
  return <div aria-hidden style={style} className={`animate-pulse rounded-md bg-gray-100 ${className}`} />
}

/** Lo que se lee en voz alta mientras se ven los esqueletos */
function LoadingLabel({ label }: { label: string }) {
  return <span className="sr-only">{label}</span>
}

/** Filas de una tabla o lista que aún no llega, dentro de una tarjeta que ya está */
export function RowsSkeleton({ rows = 4, label = 'Cargando…' }: { rows?: number; label?: string }) {
  return (
    <div role="status" className="flex flex-col gap-3">
      <LoadingLabel label={label} />
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-4">
          <Skeleton className="h-3.5 flex-1" />
          <Skeleton className="h-3.5 w-16" />
          <Skeleton className="hidden h-3.5 w-20 sm:block" />
        </div>
      ))}
    </div>
  )
}

/** Tarjeta con título y filas, mientras carga una tabla o una lista */
export function CardSkeleton({ rows = 4, label = 'Cargando…' }: { rows?: number; label?: string }) {
  return (
    <section className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
      <Skeleton className="mb-5 h-4 w-44" />
      <RowsSkeleton rows={rows} label={label} />
    </section>
  )
}

/** Tarjetas KPI vacías con la misma grilla que las reales */
export function KpiSkeletonGrid({ count, className }: { count: number; className: string }) {
  return (
    <div role="status" className={className}>
      <LoadingLabel label="Cargando indicadores…" />
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="flex flex-col gap-2 rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-5 rounded-full" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-3 w-28" />
        </div>
      ))}
    </div>
  )
}

/** Gráfica que aún no llega: barras de altura fija bajo el título */
const BAR_HEIGHTS = [45, 70, 55, 85, 40, 65, 75, 50]

export function ChartSkeleton({ height = 260 }: { height?: number }) {
  return (
    <div role="status" className="rounded-2xl border border-gray-100 bg-white p-5 shadow-lg">
      <LoadingLabel label="Cargando gráfica…" />
      <Skeleton className="h-4 w-40" />
      <Skeleton className="mt-2 h-3 w-56" />
      <div className="mt-4 flex items-end gap-3 border-b border-gray-100 px-2" style={{ height }}>
        {BAR_HEIGHTS.map((h, i) => (
          <Skeleton key={i} className="flex-1 rounded-b-none rounded-t-lg" style={{ height: `${h}%` }} />
        ))}
      </div>
    </div>
  )
}
