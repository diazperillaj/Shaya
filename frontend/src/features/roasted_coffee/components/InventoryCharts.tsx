import { useMemo, useState, type ReactNode } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import ChartCard from '../../../components/charts/ChartCard'
import CustomTooltip from '../../../components/charts/CustomTooltip'
import DonutChart from '../../../components/charts/DonutChart'
import {
  bags,
  exitsByChannel,
  exitsByProduct,
  monthlyFlow,
  monthWindow,
  OTHER_COLOR,
  productSeries,
  SERIES_COLORS,
  stockByAge,
  stockByFarmer,
  stockByProduct,
  stockByVariety,
  type StockBar,
  type StockLot,
} from '../models/inventory'
import type { InventoryEvent } from '../models/types'

/**
 * Las gráficas leen los colores del tema: rejilla y textos de los ejes en
 * gris recesivo, y un borde del color de la tarjeta que separa las barras
 * apiladas y las porciones (así también funciona en modo oscuro).
 */
const CHART_THEME = [
  '[&_.recharts-cartesian-grid_line]:[stroke:rgb(var(--border-gray-100))]',
  '[&_.recharts-cartesian-axis-tick_text]:[fill:rgb(var(--text-gray-400))]',
  '[&_.recharts-bar-rectangle_path]:[stroke:rgb(var(--bg-white))]',
  '[&_.recharts-bar-rectangle_path]:[stroke-width:2px]',
  '[&_.recharts-pie-sector_path]:[stroke:rgb(var(--bg-white))]',
].join(' ')

const TICK = { fontSize: 11 }
const CURSOR = { fill: 'rgba(0,0,0,0.04)' }

/** Texto de la leyenda en tinta del tema; el color va solo en el ícono */
const legendText = (value: string) => <span className="text-xs text-gray-600">{value}</span>

function NoData({ height = 240, children = 'Sin datos aún' }: { height?: number; children?: ReactNode }) {
  return (
    <div className="flex items-center justify-center text-sm text-gray-400" style={{ height }}>
      {children}
    </div>
  )
}

interface InventoryChartsProps {
  stock: StockLot[]
  events: InventoryEvent[]
  today: Date
}

export default function InventoryCharts({ stock, events, today }: InventoryChartsProps) {
  const months = useMemo(() => monthWindow(events, today), [events, today])
  const series = useMemo(() => productSeries(events), [events])
  const byProductMonth = useMemo(() => exitsByProduct(events, months, series), [events, months, series])
  const flow = useMemo(() => monthlyFlow(events, months), [events, months])
  const channels = useMemo(() => exitsByChannel(events, months), [events, months])
  const period = months.length === 12 ? 'Últimos 12 meses' : 'Desde el primer registro'

  return (
    <div className={`grid grid-cols-1 gap-6 xl:grid-cols-2 ${CHART_THEME}`}>
      <div className="xl:col-span-2">
        <ChartCard title="Salidas por producto" subtitle={`Bolsas que salieron cada mes · ${period}`}>
          {byProductMonth.keys.length === 0 ? (
            <NoData height={280} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={byProductMonth.data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="name" tick={TICK} axisLine={false} tickLine={false} />
                <YAxis tick={TICK} axisLine={false} tickLine={false} allowDecimals={false} width={40} />
                <Tooltip content={<CustomTooltip format={bags} />} cursor={CURSOR} />
                <Legend formatter={legendText} iconType="circle" iconSize={8} itemSorter={null} />
                {byProductMonth.keys.map((key) => (
                  <Bar
                    key={key}
                    dataKey={key}
                    stackId="exits"
                    fill={key === byProductMonth.othersKey ? OTHER_COLOR : series.get(key)}
                    maxBarSize={40}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="xl:col-span-2">
        <ChartCard title="Entradas, salidas y existencias" subtitle={`Por mes; la línea es lo que quedaba al cierre · ${period}`}>
          {flow.length === 0 ? (
            <NoData height={280} />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={flow} margin={{ top: 4, right: 8, bottom: 0, left: 0 }} barGap={2}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="name" tick={TICK} axisLine={false} tickLine={false} />
                <YAxis tick={TICK} axisLine={false} tickLine={false} allowDecimals={false} width={40} />
                <Tooltip content={<CustomTooltip format={bags} />} cursor={CURSOR} />
                <Legend formatter={legendText} iconType="circle" iconSize={8} itemSorter={null} />
                <Bar dataKey="Entradas" fill={SERIES_COLORS[0]} radius={[4, 4, 0, 0]} maxBarSize={24} />
                <Bar dataKey="Salidas" fill={SERIES_COLORS[1]} radius={[4, 4, 0, 0]} maxBarSize={24} />
                <Line
                  dataKey="Existencias"
                  type="linear"
                  stroke={SERIES_COLORS[2]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <ChartCard title="Disponible por producto" subtitle="Bolsas en bodega sumando todos los lotes">
        <HorizontalBars bars={stockByProduct(stock)} empty="Sin existencias" />
      </ChartCard>

      <ChartCard title="¿Por dónde sale el café?" subtitle={`Bolsas por canal de salida · ${period}`}>
        <DonutChart
          chart={{ data: channels.map((c) => ({ name: c.name, Salidas: c.value })), keys: ['Salidas'] }}
          colors={channels.map((c) => c.color)}
          format={bags}
        />
      </ChartCard>

      <StockByOrigin stock={stock} />

      <ChartCard title="Antigüedad del inventario" subtitle="Bolsas disponibles según los días desde el proceso">
        {stock.length === 0 ? (
          <NoData>Sin existencias</NoData>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={stockByAge(stock)} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="name" tick={TICK} axisLine={false} tickLine={false} interval={0} />
              <YAxis tick={TICK} axisLine={false} tickLine={false} allowDecimals={false} width={40} />
              <Tooltip content={<CustomTooltip format={bags} />} cursor={CURSOR} />
              <Bar dataKey="value" name="Disponible" fill={SERIES_COLORS[0]} radius={[4, 4, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  )
}

const ORIGINS = [
  { id: 'variety', label: 'Variedad', group: stockByVariety },
  { id: 'farmer', label: 'Caficultor', group: stockByFarmer },
] as const

/** Existencias por variedad o por caficultor, con un selector en la cabecera */
function StockByOrigin({ stock }: { stock: StockLot[] }) {
  const [origin, setOrigin] = useState<(typeof ORIGINS)[number]['id']>('variety')
  const current = ORIGINS.find((o) => o.id === origin) ?? ORIGINS[0]

  const toggle = (
    <div role="radiogroup" aria-label="Agrupar por" className="inline-flex shrink-0 rounded-lg bg-gray-100 p-0.5 text-xs font-medium">
      {ORIGINS.map((o) => {
        const active = o.id === origin
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => setOrigin(o.id)}
            className={`rounded-md px-2.5 py-1 transition-colors duration-150 ${
              active ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )

  return (
    <ChartCard
      title={`Disponible por ${current.label.toLowerCase()}`}
      subtitle="Bolsas en bodega según el origen del lote"
      action={toggle}
    >
      <HorizontalBars bars={current.group(stock)} empty="Sin existencias" />
    </ChartCard>
  )
}

function HorizontalBars({ bars, empty }: { bars: StockBar[]; empty: string }) {
  if (bars.length === 0) return <NoData>{empty}</NoData>
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, bars.length * 36 + 24)}>
      <BarChart data={bars} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid horizontal={false} />
        <XAxis type="number" tick={TICK} axisLine={false} tickLine={false} allowDecimals={false} />
        <YAxis dataKey="name" type="category" tick={TICK} axisLine={false} tickLine={false} width={120} />
        <Tooltip content={<CustomTooltip format={bags} />} cursor={CURSOR} />
        <Bar dataKey="value" name="Disponible" fill={SERIES_COLORS[0]} radius={[0, 4, 4, 0]} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  )
}
