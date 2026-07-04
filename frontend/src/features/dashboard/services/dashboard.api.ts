import type { DashboardChartsApi, DashboardKPIsApi } from '../models/types'

const BASE = '/api/v1/dashboard'

export const fetchDashboardKpis = async (): Promise<DashboardKPIsApi> => {
  const res = await fetch(`${BASE}/kpis`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo KPIs')
  return res.json()
}

export const fetchDashboardCharts = async (): Promise<DashboardChartsApi> => {
  const res = await fetch(`${BASE}/charts`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo datos de gráficos')
  return res.json()
}
