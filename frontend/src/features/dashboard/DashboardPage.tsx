import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  ShoppingCart,
  Package,
  Wheat,
  RefreshCw,
  Coffee,
  AlertCircle,
  Receipt,
  Scale,
} from 'lucide-react'
import { useDashboard } from './hooks/useDashboard'
import type { DashboardKPIsApi, RechartsChart } from './models/types'

// ─── Helpers ─────────────────────────────────────────────────────────────────

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const fmtNum = (n: number) => n.toLocaleString('es-CO')

// ─── Chart colors ─────────────────────────────────────────────────────────────

// Gradient IDs for vertical bars (top → bottom) and horizontal bars (left → right)
const GRAD_V = ['url(#gv0)', 'url(#gv1)', 'url(#gv2)', 'url(#gv3)']
const GRAD_H = ['url(#gh0)', 'url(#gh1)', 'url(#gh2)', 'url(#gh3)']

// Palette for pie/donut slices
const PIE_COLORS = [
  '#065f46', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0',
  '#0d9488', '#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4',
  '#047857', '#059669', '#0f766e',
]

// Rendered once outside Recharts — SVG gradient IDs are global in the browser
function GlobalChartDefs() {
  return (
    <svg width="0" height="0" style={{ position: 'absolute', overflow: 'hidden' }} aria-hidden>
      <defs>
        <linearGradient id="gv0" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#065f46" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gv1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#34d399" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#059669" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gv2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6ee7b7" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#34d399" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gv3" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a7f3d0" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#6ee7b7" stopOpacity={1} />
        </linearGradient>
        <linearGradient id="gh1" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#34d399" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#059669" stopOpacity={1} />
        </linearGradient>
      </defs>
    </svg>
  )
}

// ─── Custom tooltip ───────────────────────────────────────────────────────────

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
}

function CustomTooltip({ active, payload, label, currency = false }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null

  const fmt = (v: number) =>
    currency
      ? fmtCOP(v)
      : v.toLocaleString('es-CO')

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-2xl px-4 py-3 min-w-[160px] border border-white/10">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">{label}</p>
      <div className="flex flex-col gap-1.5">
        {payload.map((item) => (
          <div key={item.name} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-gray-300">{item.name}</span>
            </div>
            <span className="text-xs font-bold text-white">{fmt(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { kpis, charts, loading, error, refresh } = useDashboard()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-3 text-emerald-700">
        <span className="animate-spin w-6 h-6 border-2 border-emerald-700 border-t-transparent rounded-full inline-block" />
        Cargando dashboard…
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4 text-red-600">
        <AlertCircle className="w-10 h-10" />
        <p className="text-sm font-medium">{error}</p>
        <button
          onClick={refresh}
          className="flex items-center gap-2 bg-emerald-900 text-white px-4 py-2 rounded-xl text-sm hover:bg-emerald-800 transition-colors"
        >
          <RefreshCw className="w-4 h-4" /> Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <GlobalChartDefs />

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold">Dashboard</h1>
        <button
          onClick={refresh}
          className="flex items-center gap-2 text-sm bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-xl shadow-sm hover:shadow-md transition-all duration-200"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      {/* ── KPI cards ──────────────────────────────────────────────────────── */}
      {kpis && <KpiGrid kpis={kpis} />}

      {/* ── Charts ─────────────────────────────────────────────────────────── */}
      {charts && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

          {/* Chart 1: Sales by month */}
          <ChartCard title="Ingresos por mes" subtitle="Últimos 6 meses">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={charts.salesByMonth.data} margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip currency />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
                <Legend />
                <Bar yAxisId="left" dataKey="Ingresos ($)" fill={GRAD_V[0]} radius={[8, 8, 0, 0]} maxBarSize={40} />
                <Bar yAxisId="right" dataKey="N° ventas" fill={GRAD_V[2]} radius={[8, 8, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Chart 2: Top products */}
          <ChartCard title="Top productos vendidos" subtitle="Por unidades vendidas">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={charts.topProducts.data}
                layout="vertical"
                margin={{ top: 4, right: 16, bottom: 0, left: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
                <Legend />
                <Bar dataKey="Unidades vendidas" fill={GRAD_H[1]} radius={[0, 8, 8, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Chart: Ingresos vs Gastos vs Utilidad — full width */}
          <div className="xl:col-span-2">
            <ChartCard title="Ingresos vs Gastos" subtitle="Ingresos, gastos generales y utilidad · Últimos 6 meses">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={charts.incomeVsExpenses.data} margin={{ top: 4, right: 16, bottom: 0, left: 8 }} barCategoryGap="25%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip currency />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
                  <Legend />
                  <Bar dataKey="Ingresos" fill="#059669" radius={[8, 8, 0, 0]} maxBarSize={36} />
                  <Bar dataKey="Gastos" fill="#dc2626" radius={[8, 8, 0, 0]} maxBarSize={36} />
                  <Bar dataKey="Utilidad" fill="#0d9488" radius={[8, 8, 0, 0]} maxBarSize={36} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Chart: Gastos por categoría (donut) */}
          <ChartCard title="Gastos por categoría" subtitle="Distribución del gasto acumulado">
            <DonutChart chart={charts.expensesByCategory} />
          </ChartCard>

          {/* Chart: Ventas por método de pago (donut) */}
          <ChartCard title="Ventas por método de pago" subtitle="Total vendido por Efectivo, Nequi, Nu…">
            <DonutChart chart={charts.salesByPaymentMethod} />
          </ChartCard>

          {/* Chart 3: Inventory status — full width */}
          <div className="xl:col-span-2">
            <ChartCard title="Estado del inventario tostado" subtitle="Total producido · Disponible · Vendido por producto">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={charts.inventoryStatus.data} margin={{ top: 4, right: 16, bottom: 0, left: 8 }} barCategoryGap="25%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0fdf4" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)', radius: 6 }} />
                  <Legend />
                  <Bar dataKey="Total producido" fill={GRAD_V[0]} radius={[8, 8, 0, 0]} maxBarSize={36} />
                  <Bar dataKey="Disponible" fill={GRAD_V[2]} radius={[8, 8, 0, 0]} maxBarSize={36} />
                  <Bar dataKey="Vendido" fill={GRAD_V[3]} radius={[8, 8, 0, 0]} maxBarSize={36} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

        </div>
      )}
    </div>
  )
}

// ─── Donut chart (categorías / métodos de pago) ───────────────────────────────

function DonutChart({ chart }: { chart: RechartsChart }) {
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
              return [`${fmtCOP(v)} (${((v / total) * 100).toFixed(1)}%)`, String(name)]
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
              {fmtCOP(d.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── KPI grid ─────────────────────────────────────────────────────────────────

function KpiGrid({ kpis }: { kpis: DashboardKPIsApi }) {
  const roastedPct =
    kpis.roasted_bags_total > 0
      ? Math.round((kpis.roasted_bags_available / kpis.roasted_bags_total) * 100)
      : 0

  // Variación de gastos vs mes anterior
  const expenseVariation =
    kpis.expenses_total_prev_month > 0
      ? ((kpis.expenses_total_month - kpis.expenses_total_prev_month) /
          kpis.expenses_total_prev_month) * 100
      : null
  const expenseSub =
    expenseVariation === null
      ? `${kpis.expenses_count_month} gasto${kpis.expenses_count_month === 1 ? '' : 's'} este mes`
      : `${expenseVariation >= 0 ? '+' : ''}${expenseVariation.toFixed(0)}% vs mes anterior`

  // Ticket promedio y margen del mes (calculados en el front)
  const avgTicket =
    kpis.sales_count_month > 0 ? kpis.sales_total_month / kpis.sales_count_month : 0
  const marginMonth =
    kpis.sales_total_month > 0 ? (kpis.net_month / kpis.sales_total_month) * 100 : null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <KpiCard
        icon={<Coffee className="w-5 h-5" />}
        label="Precio café"
        value={kpis.coffee_price_raw}
        sub="Bolsa 125 kg · COP"
        accent
      />
      <KpiCard
        icon={<TrendingUp className="w-5 h-5" />}
        label="Ventas este mes"
        value={fmtCOP(kpis.sales_total_month)}
        sub={`${kpis.sales_count_month} ${kpis.sales_count_month === 1 ? 'venta' : 'ventas'}`}
      />
      <KpiCard
        icon={<ShoppingCart className="w-5 h-5" />}
        label="Total acumulado"
        value={fmtCOP(kpis.sales_total_all_time)}
        sub={`${kpis.sales_count_all_time} ventas en total`}
      />
      <KpiCard
        icon={<Package className="w-5 h-5" />}
        label="Inventario tostado"
        value={`${fmtNum(kpis.roasted_bags_available)} bolsas`}
        sub={`${roastedPct}% disponible`}
      />
      <KpiCard
        icon={<Wheat className="w-5 h-5" />}
        label="Pergamino disponible"
        value={`${kpis.parchment_available_kg.toFixed(1)} kg`}
        sub="Stock pergamino seco"
      />
      <KpiCard
        icon={<TrendingUp className="w-5 h-5" />}
        label="Bolsas producidas"
        value={fmtNum(kpis.roasted_bags_total)}
        sub={`${fmtNum(kpis.roasted_bags_total - kpis.roasted_bags_available)} vendidas`}
      />
      <KpiCard
        icon={<Receipt className="w-5 h-5" />}
        label="Gastos este mes"
        value={fmtCOP(kpis.expenses_total_month)}
        sub={expenseSub}
      />
      <KpiCard
        icon={kpis.net_month >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
        label="Utilidad del mes"
        value={fmtCOP(kpis.net_month)}
        sub="Ventas − gastos del mes"
      />
      <KpiCard
        icon={<Scale className="w-5 h-5" />}
        label="Después de gastos"
        value={fmtCOP(kpis.net_all_time)}
        sub="Utilidad histórica acumulada"
      />
      <KpiCard
        icon={<Receipt className="w-5 h-5" />}
        label="Gastos acumulados"
        value={fmtCOP(kpis.expenses_total_all_time)}
        sub="Total histórico de gastos"
      />
      <KpiCard
        icon={<ShoppingCart className="w-5 h-5" />}
        label="Ticket promedio"
        value={fmtCOP(avgTicket)}
        sub={kpis.sales_count_month > 0 ? 'Promedio por venta este mes' : 'Sin ventas este mes'}
      />
      <KpiCard
        icon={marginMonth === null || marginMonth >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
        label="Margen del mes"
        value={marginMonth === null ? '—' : `${marginMonth.toFixed(1)}%`}
        sub="Utilidad / ventas del mes"
      />
    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────

interface KpiCardProps {
  icon: React.ReactNode
  label: string
  value: string
  sub: string
  accent?: boolean
}

function KpiCard({ icon, label, value, sub, accent = false }: KpiCardProps) {
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

interface ChartCardProps {
  title: string
  subtitle: string
  children: React.ReactNode
}

function ChartCard({ title, subtitle, children }: ChartCardProps) {
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
