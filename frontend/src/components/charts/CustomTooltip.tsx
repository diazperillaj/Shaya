import { fmtCOP } from './chartData'

interface TooltipPayloadItem {
  name: string
  value: number
  color: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayloadItem[]
  label?: string
  currency?: boolean
  /** Formato propio de los valores (kg, %…); tiene prioridad sobre `currency` */
  format?: (value: number) => string
}

export default function CustomTooltip({ active, payload, label, currency = false, format }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null

  const fmt = (v: number) =>
    format
      ? format(v)
      : currency
        ? fmtCOP(v)
        : v.toLocaleString('es-CO')

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-2xl px-4 py-3 min-w-[160px] border border-white/10 dark:border-gray-300">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">{label}</p>
      <div className="flex flex-col gap-1.5">
        {payload.map((item) => (
          <div key={item.name} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-gray-300 dark:text-gray-600">{item.name}</span>
            </div>
            <span className="text-xs font-bold text-white">{fmt(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
