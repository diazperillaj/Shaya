// ─── Raw API shapes ───────────────────────────────────────────────────────────

export interface DashboardKPIsApi {
  sales_total_month: number
  sales_count_month: number
  sales_total_all_time: number
  sales_count_all_time: number
  parchment_available_kg: number
  roasted_bags_available: number
  roasted_bags_total: number
  coffee_price_raw: string
  coffee_price_value: number | null
}

export interface ChartSeriesApi {
  name: string
  data: number[]
}

export interface BarChartDataApi {
  labels: string[]
  series: ChartSeriesApi[]
}

export interface DashboardChartsApi {
  sales_by_month: BarChartDataApi
  top_products: BarChartDataApi
  inventory_status: BarChartDataApi
}

// ─── Recharts-ready shape ─────────────────────────────────────────────────────
// Each entry: { name: label, [seriesName]: value, ... }

export type RechartsDataPoint = Record<string, string | number>

export interface RechartsChart {
  data: RechartsDataPoint[]
  keys: string[]   // series names → used as <Bar dataKey="..." />
}

export interface DashboardCharts {
  salesByMonth: RechartsChart
  topProducts: RechartsChart
  inventoryStatus: RechartsChart
}
