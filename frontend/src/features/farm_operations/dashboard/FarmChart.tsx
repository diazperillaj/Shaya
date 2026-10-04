import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import CustomTooltip from '../../../components/charts/CustomTooltip'
import { GRAD_V, toRecharts, type BarChartDataApi } from '../../../components/charts/chartData'

const LINE_COLORS = ['#b45309', '#0d9488', '#6366f1']
const STACK_COLORS = ['#065f46', '#10b981', '#6ee7b7', '#0d9488']
const OUT_OF_RANGE = '#f59e0b'

export function NoData({ height = 220 }: { height?: number }) {
  return (
    <div className="flex items-center justify-center text-sm text-gray-400" style={{ height }}>
      Sin datos en el periodo
    </div>
  )
}

/**
 * Gráfica del dashboard sobre el contrato `BarChartData`: barras verticales u
 * horizontales, apiladas o agrupadas, con series como línea (un umbral), un
 * eje derecho para otra escala y una línea de referencia.
 */
export default function FarmChart({
  chart,
  format,
  horizontal = false,
  stacked = false,
  lines = [],
  rightAxis = [],
  reference,
  highlight,
  height,
  asLine = false,
  zoom = false,
}: {
  chart: BarChartDataApi
  format: (value: number) => string
  horizontal?: boolean
  stacked?: boolean
  /** Series que se dibujan como línea (umbrales) */
  lines?: string[]
  /** Series en el eje derecho (otra escala) */
  rightAxis?: string[]
  reference?: { value: number; label: string }
  /** Barras resaltadas como dentro del rango; las demás, en ámbar */
  highlight?: (label: string) => boolean
  height?: number
  /** Todas las series como líneas (evolución en el tiempo) */
  asLine?: boolean
  /** Eje de valores ajustado a los datos (no desde 0), para ver diferencias pequeñas */
  zoom?: boolean
}) {
  if (chart.labels.length === 0 || chart.series.length === 0) return <NoData height={height} />
  const { data, keys } = toRecharts(chart)
  const size = height ?? (horizontal ? Math.max(220, chart.labels.length * 30 + 60) : 260)
  const hasRight = rightAxis.length > 0
  const values = chart.series.flatMap((s) => s.data).concat(reference ? [reference.value] : [])
  const domain: [number, number] | undefined = zoom
    ? [Math.max(0, Math.floor(Math.min(...values)) - 1), Math.ceil(Math.max(...values)) + 1]
    : undefined

  const valueAxis = horizontal
    ? <XAxis type="number" domain={domain} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => format(Number(v))} />
    : <YAxis yAxisId="left" domain={domain} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => format(Number(v))} width={70} />
  const categoryAxis = horizontal
    ? <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={110} axisLine={false} tickLine={false} />
    : <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />

  return (
    <ResponsiveContainer width="100%" height={size}>
      <ComposedChart
        data={data}
        layout={horizontal ? 'vertical' : 'horizontal'}
        margin={{ top: 8, right: hasRight ? 8 : 16, bottom: 0, left: horizontal ? 8 : 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={horizontal} horizontal={!horizontal} />
        {categoryAxis}
        {valueAxis}
        {hasRight && !horizontal && (
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={50} />
        )}
        <Tooltip content={<CustomTooltip format={format} />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        {keys.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
        {reference && (
          <ReferenceLine
            {...(horizontal ? { x: reference.value } : { y: reference.value, yAxisId: 'left' })}
            stroke="#b45309"
            strokeDasharray="4 4"
            label={{ value: reference.label, fontSize: 11, fill: '#b45309', position: 'insideTopRight' }}
          />
        )}
        {keys.map((key, index) => {
          const axis = horizontal ? {} : { yAxisId: rightAxis.includes(key) ? 'right' : 'left' }
          if (asLine || lines.includes(key)) {
            return (
              <Line
                key={key}
                {...axis}
                type={asLine ? 'monotone' : 'stepAfter'}
                dataKey={key}
                stroke={LINE_COLORS[index % LINE_COLORS.length]}
                strokeWidth={2}
                strokeDasharray={asLine ? undefined : '5 4'}
                isAnimationActive={false}
                dot={asLine}
              />
            )
          }
          return (
            <Bar
              key={key}
              {...axis}
              dataKey={key}
              stackId={stacked ? 'stack' : undefined}
              fill={stacked ? STACK_COLORS[index % STACK_COLORS.length] : GRAD_V[index % GRAD_V.length]}
              radius={stacked ? 0 : horizontal ? [0, 8, 8, 0] : [8, 8, 0, 0]}
              maxBarSize={horizontal ? 24 : 36}
              isAnimationActive={false}
            >
              {highlight &&
                data.map((point) => (
                  <Cell key={String(point.name)} fill={highlight(String(point.name)) ? GRAD_V[0] : OUT_OF_RANGE} />
                ))}
            </Bar>
          )
        })}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
