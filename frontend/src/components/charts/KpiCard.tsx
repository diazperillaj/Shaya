import type { ReactNode } from 'react'

interface KpiCardProps {
  icon: ReactNode
  label: string
  value: string
  sub: string
  accent?: boolean
}

export default function KpiCard({ icon, label, value, sub, accent = false }: KpiCardProps) {
  return (
    <div
      className={`rounded-2xl p-4 border shadow-sm flex flex-col gap-2 ${
        accent
          ? 'bg-emerald-900 border-emerald-800 text-white'
          : 'bg-white border-gray-100'
      }`}
    >
      <div className={`flex items-center gap-2 ${accent ? 'text-emerald-300' : 'text-emerald-700'}`}>
        {icon}
        <span className={`text-xs font-semibold uppercase tracking-wide ${accent ? 'text-emerald-200' : 'text-gray-500'}`}>
          {label}
        </span>
      </div>
      <p className={`text-lg font-bold leading-tight ${accent ? 'text-white' : 'text-gray-900'}`}>
        {value}
      </p>
      <p className={`text-xs ${accent ? 'text-emerald-300' : 'text-gray-400'}`}>{sub}</p>
    </div>
  )
}
