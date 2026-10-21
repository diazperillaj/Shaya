import type { ReactNode } from 'react'
import { BusyOverlay } from '../ui/Busy'

interface ChartCardProps {
  title: string
  subtitle: string
  children: ReactNode
  /** Control junto al título (p. ej. cambiar la agrupación) */
  action?: ReactNode
}

export default function ChartCard({ title, subtitle, children, action }: ChartCardProps) {
  return (
    <div className="relative bg-white rounded-2xl shadow-lg border border-gray-100 p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
          <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
        </div>
        {action}
      </div>
      {children}
      <BusyOverlay />
    </div>
  )
}
