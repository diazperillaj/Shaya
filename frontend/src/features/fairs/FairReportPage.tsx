import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import {
  ArrowLeft, RefreshCw, TrendingUp, TrendingDown, ShoppingBag,
  Package, Clock, BarChart2, AlertCircle,
} from 'lucide-react'
import { fetchFairReport } from './services/fairs.api'
import type { FairReport } from './models/types'

interface Props {
  fairId: number
  fairName: string
  onBack: () => void
}

const fmtCOP = (n: number | string) =>
  Number(n).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const PIE_COLORS = ['#065f46', '#059669', '#34d399', '#a7f3d0']

function GlobalDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute', overflow: 'hidden' }} aria-hidden>
      <defs>
        <linearGradient id="fgv0" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#065f46" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="fgv1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#34d399" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#059669" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="fgv2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6ee7b7" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#34d399" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="fgv3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f87171" stopOpacity={0.9} />
          <stop offset="100%" stopColor="#b91c1c" stopOpacity={1} />
        </linearGradient>
      </defs>
    </svg>
  )
}

interface TooltipItem { name: string; value: number; color?: string; fill?: string }
function CustomTooltip({ active, payload, label, currency = false }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-2xl px-4 py-3 min-w-[160px] border border-white/10">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">{label}</p>
      {payload.map((item: TooltipItem) => (
        <div key={item.name} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.fill ?? item.color }} />
            <span className="text-xs text-gray-300">{item.name}</span>
          </div>
          <span className="text-xs font-bold text-white">
            {currency ? fmtCOP(item.value) : item.value.toLocaleString('es-CO')}
          </span>
        </div>
      ))}
    </div>
  )
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
        <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
      </div>
      {children}
    </div>
  )
}

function KpiCard({ icon, label, value, sub, color = 'default' }: {
  icon: React.ReactNode; label: string; value: string; sub: string
  color?: 'default' | 'green' | 'red' | 'blue' | 'accent'
}) {
  const styles = {
    default: 'bg-white border-gray-100',
    green: 'bg-emerald-50 border-emerald-200',
    red: 'bg-red-50 border-red-200',
    blue: 'bg-sky-50 border-sky-200',
    accent: 'bg-emerald-900 border-emerald-800 text-white',
  }
  const iconStyle = {
    default: 'text-emerald-700',
    green: 'text-emerald-700',
    red: 'text-red-600',
    blue: 'text-sky-600',
    accent: 'text-emerald-300',
  }
  const valueStyle = {
    default: 'text-gray-900',
    green: 'text-emerald-800',
    red: 'text-red-700',
    blue: 'text-sky-800',
    accent: 'text-white',
  }
  const subStyle = {
    default: 'text-gray-400',
    green: 'text-emerald-600',
    red: 'text-red-500',
    blue: 'text-sky-500',
    accent: 'text-emerald-300',
  }

  return (
    <div className={`rounded-2xl p-4 border shadow-sm flex flex-col gap-2 ${styles[color]}`}>
      <div className={`flex items-center gap-2 ${iconStyle[color]}`}>
        {icon}
        <span className={`text-xs font-semibold uppercase tracking-wide ${color === 'accent' ? 'text-emerald-200' : 'text-gray-500'}`}>{label}</span>
      </div>
      <p className={`text-lg font-bold leading-tight ${valueStyle[color]}`}>{value}</p>
      <p className={`text-xs ${subStyle[color]}`}>{sub}</p>
    </div>
  )
}

export default function FairReportPage({ fairId, fairName, onBack }: Props) {
  const [report, setReport] = useState<FairReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true); setError(null)
    try { setReport(await fetchFairReport(fairId)) }
    catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [fairId])

  if (loading) return (
    <div className="flex items-center justify-center h-64 gap-3 text-emerald-700">
      <span className="animate-spin w-6 h-6 border-2 border-emerald-700 border-t-transparent rounded-full inline-block" />
      Cargando reporte…
    </div>
  )

  if (error) return (
    <div className="flex flex-col items-center justify-center h-64 gap-4 text-red-600">
      <AlertCircle className="w-10 h-10" />
      <p className="text-sm font-medium">{error}</p>
      <button onClick={load} className="flex items-center gap-2 bg-emerald-900 text-white px-4 py-2 rounded-xl text-sm">
        <RefreshCw className="w-4 h-4" /> Reintentar
      </button>
    </div>
  )

  if (!report) return null

  const { kpis, salesByProduct, salesTimeline, expensesByCategory, inventoryStatus } = report
  const margin = parseFloat(kpis.margin_percentage)
  const pieData = expensesByCategory.labels.map((label, i) => ({ name: label, value: expensesByCategory.data[i] }))

  return (
    <div className="flex flex-col gap-6">
      <GlobalDefs />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 rounded-xl hover:bg-gray-100 transition-colors">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Reporte — {fairName}</h1>
            <p className="text-sm text-gray-400">Dashboard de resultados</p>
          </div>
        </div>
        <button onClick={load}
          className="flex items-center gap-2 text-sm bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-xl shadow-sm transition-all">
          <RefreshCw className="w-4 h-4" /> Actualizar
        </button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard icon={<TrendingUp className="w-5 h-5" />} label="Total ventas"
          value={fmtCOP(kpis.total_sales)} sub={`${kpis.total_transactions} transacciones`} color="green" />
        <KpiCard icon={<TrendingDown className="w-5 h-5" />} label="Total gastos"
          value={fmtCOP(kpis.total_expenses)} sub="Alimentación, insumos, transporte" color="red" />
        <KpiCard icon={<BarChart2 className="w-5 h-5" />} label="Ganancia neta"
          value={fmtCOP(kpis.net_profit)}
          sub={`Margen: ${margin.toFixed(1)}%`}
          color={parseFloat(kpis.net_profit) >= 0 ? 'accent' : 'red'} />
        <KpiCard icon={<ShoppingBag className="w-5 h-5" />} label="Venta promedio"
          value={fmtCOP(kpis.avg_sale_value)} sub="Por transacción" color="blue" />
        <KpiCard icon={<Package className="w-5 h-5" />} label="Inventario"
          value={`${kpis.total_bags_sold} / ${kpis.total_bags_assigned}`}
          sub={`${parseFloat(kpis.inventory_utilization_percentage).toFixed(1)}% utilizado`} />
        <KpiCard icon={<Clock className="w-5 h-5" />} label="Duración"
          value={kpis.duration_hours != null ? `${kpis.duration_hours.toFixed(1)} h` : 'En curso'}
          sub={kpis.duration_hours != null ? 'Duración total de la feria' : 'Feria aún abierta'} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

        {/* Ventas por producto */}
        <ChartCard title="Ventas por producto" subtitle="Unidades vendidas e ingresos">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={salesByProduct.data} margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
              <Legend />
              <Bar yAxisId="left" dataKey="Unidades vendidas" fill="url(#fgv0)" radius={[8, 8, 0, 0]} maxBarSize={40} />
              <Bar yAxisId="right" dataKey="Ingresos ($)" fill="url(#fgv1)" radius={[8, 8, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Timeline de ventas */}
        <ChartCard title="Timeline de ventas" subtitle="Evolución durante la feria">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={salesTimeline.data} margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip currency />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
              <Legend />
              <Bar yAxisId="left" dataKey="Ingresos ($)" fill="url(#fgv0)" radius={[8, 8, 0, 0]} maxBarSize={40} />
              <Bar yAxisId="right" dataKey="N° ventas" fill="url(#fgv2)" radius={[8, 8, 0, 0]} maxBarSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Gastos por categoría */}
        <ChartCard title="Gastos por categoría" subtitle="Distribución del gasto total">
          {pieData.every(d => d.value === 0) ? (
            <div className="flex items-center justify-center h-[220px] text-gray-400 text-sm">Sin gastos registrados</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${((percent as number) * 100).toFixed(0)}%`} labelLine={false}>
                  {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip currency />} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* Estado del inventario */}
        <ChartCard title="Estado del inventario" subtitle="Inicial · Vendido · Remanente por producto">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              data={inventoryStatus.map(i => ({
                name: i.product_name,
                'Inicial': i.initial_quantity,
                'Vendido': i.sold_quantity,
                'Remanente': i.remaining_quantity,
              }))}
              margin={{ top: 4, right: 16, bottom: 0, left: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
              <Legend />
              <Bar dataKey="Inicial" fill="url(#fgv1)" radius={[6, 6, 0, 0]} maxBarSize={32} />
              <Bar dataKey="Vendido" fill="url(#fgv0)" radius={[6, 6, 0, 0]} maxBarSize={32} />
              <Bar dataKey="Remanente" fill="url(#fgv2)" radius={[6, 6, 0, 0]} maxBarSize={32} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

      </div>

      {/* Inventory detail table */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-5">
        <h3 className="text-sm font-semibold text-gray-800 mb-1">Detalle de inventario</h3>
        <p className="text-xs text-gray-400 mb-4">Resultados por producto al cierre</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                {['Producto', 'Inicial', 'Vendido', 'Remanente', '% Utilización', 'Ingresos'].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wide pb-2 pr-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {inventoryStatus.map((item, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="py-2.5 pr-4 font-medium text-gray-800">{item.product_name}</td>
                  <td className="py-2.5 pr-4 text-gray-600">{item.initial_quantity}</td>
                  <td className="py-2.5 pr-4 text-emerald-700 font-semibold">{item.sold_quantity}</td>
                  <td className="py-2.5 pr-4 text-gray-600">{item.remaining_quantity}</td>
                  <td className="py-2.5 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-1.5">
                        <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: `${parseFloat(item.utilization_percentage)}%` }} />
                      </div>
                      <span className="text-xs text-gray-600">{parseFloat(item.utilization_percentage).toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="py-2.5 pr-4 font-semibold text-gray-800">{fmtCOP(Number(item.revenue))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
