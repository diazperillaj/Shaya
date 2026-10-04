import { useEffect, useState } from 'react'
import { fetchDashboardCharts, fetchDashboardKpis } from '../services/dashboard.api'
import { toRecharts } from '../../../components/charts/chartData'
import type { DashboardCharts, DashboardKPIsApi } from '../models/types'

// ─── Hook ─────────────────────────────────────────────────────────────────────

interface UseDashboardResult {
  kpis: DashboardKPIsApi | null
  charts: DashboardCharts | null
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useDashboard(): UseDashboardResult {
  const [kpis, setKpis] = useState<DashboardKPIsApi | null>(null)
  const [charts, setCharts] = useState<DashboardCharts | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [kpisData, chartsData] = await Promise.all([
          fetchDashboardKpis(),
          fetchDashboardCharts(),
        ])
        if (!cancelled) {
          setKpis(kpisData)
          setCharts({
            salesByMonth: toRecharts(chartsData.sales_by_month),
            topProducts: toRecharts(chartsData.top_products),
            inventoryStatus: toRecharts(chartsData.inventory_status),
            incomeVsExpenses: toRecharts(chartsData.income_vs_expenses),
            expensesByCategory: toRecharts(chartsData.expenses_by_category),
            salesByPaymentMethod: toRecharts(chartsData.sales_by_payment_method),
          })
        }
      } catch (err: any) {
        if (!cancelled) setError(err.message ?? 'Error cargando el dashboard')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [tick])

  return { kpis, charts, loading, error, refresh: () => setTick((t) => t + 1) }
}
