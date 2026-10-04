import type {
  CycleState,
  DashboardSummary,
  FarmAlert,
  FarmRanking,
  ProductionCharts,
  QualityCharts,
  Season,
} from '../models/types'
import { request } from './http'

/* Dashboard del cultivo: los agregados llegan como números */

export interface DashboardScope {
  farmId: number | null
  from: string
  to: string
}

const periodQuery = ({ farmId, from, to }: DashboardScope) => ({ farm_id: farmId, date_from: from, date_to: to })

export const fetchDashboardSummary = (scope: DashboardScope): Promise<DashboardSummary> =>
  request('/dashboard/summary', 'Error obteniendo el resumen', { query: periodQuery(scope) })

export const fetchDashboardAlerts = (farmId: number | null): Promise<FarmAlert[]> =>
  request('/dashboard/alerts', 'Error obteniendo las alertas', { query: { farm_id: farmId } })

export const fetchProductionCharts = (scope: DashboardScope): Promise<ProductionCharts> =>
  request('/dashboard/production', 'Error obteniendo la producción', { query: periodQuery(scope) })

export const fetchQualityCharts = (scope: DashboardScope): Promise<QualityCharts> =>
  request('/dashboard/quality', 'Error obteniendo la calidad', { query: periodQuery(scope) })

export const fetchSeasons = (farmId: number | null): Promise<Season[]> =>
  request('/dashboard/periods', 'Error obteniendo las temporadas', { query: { farm_id: farmId } })

export const fetchCycleStates = (farmId: number | null): Promise<CycleState[]> =>
  request('/dashboard/cycles', 'Error obteniendo los ciclos', { query: { farm_id: farmId } })

export const fetchFarmRanking = (from: string, to: string): Promise<FarmRanking[]> =>
  request('/dashboard/farms', 'Error obteniendo las fincas', { query: { date_from: from, date_to: to } })
