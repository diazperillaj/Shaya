import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { fmtCOP, PIE_COLORS, type RechartsChart } from './chartData'

// ─── Donut chart (categorías / métodos de pago) ───────────────────────────────

export default function DonutChart({
  chart,
  format = fmtCOP,
}: {
  chart: RechartsChart
  /** Formato de los valores; por defecto, pesos */
  format?: (value: number) => string
}) {
  const valueKey = chart.keys[0]
  const data = chart.data.map((d) => ({ name: String(d.name), value: Number(d[valueKey] ?? 0) }))
  const total = data.reduce((sum, d) => sum + d.value, 0)

  if (total <= 0) {
    return (
      <div className="flex items-center justify-center h-[260px] text-sm text-gray-400">
        Sin datos aún
      </div>
    )
  }

  return (
    <div className="flex flex-col lg:flex-row items-center gap-4">
      <ResponsiveContainer width="100%" height={260} className="lg:flex-1">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="55%"
            outerRadius="85%"
            paddingAngle={2}
            strokeWidth={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name) => {
              const v = Number(value ?? 0)
              return [`${format(v)} (${((v / total) * 100).toFixed(1)}%)`, String(name)]
            }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend with values */}
      <div className="flex flex-col gap-1.5 max-h-[240px] overflow-y-auto pr-1 min-w-[180px]">
        {data.map((d, i) => (
          <div key={d.name} className="flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-1.5 min-w-0">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
              />
              <span className="text-gray-600 truncate">{d.name}</span>
            </div>
            <span className="font-semibold text-gray-800 whitespace-nowrap">
              {format(d.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
