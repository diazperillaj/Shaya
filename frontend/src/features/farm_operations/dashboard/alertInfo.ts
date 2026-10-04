import type { AlertSeverity, FarmAlert } from '../models/types'

/** Nombre corto de cada tipo de alerta (dashboards-alertas §4) */
export const ALERT_LABELS: Record<string, string> = {
  fertilization_due: 'Fertilización',
  phytosanitary_due: 'Muestreo de plagas',
  weeding_due: 'Deshierba',
  irrigation_due: 'Riego',
  harvest_pass_due: 'Próxima pasada',
  cycle_inactive: 'Ciclo sin registros',
  humidity_out_of_range: 'Humedad final',
  fermentation_out_of_range: 'Fermentación',
  harvest_without_quality: 'Cosecha sin evaluar',
  drying_without_quality: 'Secado sin evaluar',
  yield_below_history: 'Rendimiento bajo',
  broca_above_threshold: 'Broca',
  drying_too_long: 'Secado largo',
  processing_stalled: 'Fermentación en curso',
  unpaid_labor: 'Pagos pendientes',
  harvest_open_too_long: 'Pasada abierta',
}

export const SEVERITY_INFO: Record<AlertSeverity, { label: string; plural: string; dot: string; badge: string }> = {
  high: { label: 'Riesgo', plural: 'Riesgos', dot: 'bg-red-500', badge: 'bg-red-50 text-red-700 border-red-100' },
  medium: { label: 'Desvío', plural: 'Desvíos', dot: 'bg-amber-500', badge: 'bg-amber-50 text-amber-800 border-amber-100' },
  info: { label: 'Recordatorio', plural: 'Recordatorios', dot: 'bg-sky-500', badge: 'bg-sky-50 text-sky-800 border-sky-100' },
}

/** Ruta del módulo a la que lleva cada alerta (plan de implementación, 2.6) */
export function alertLink(alert: FarmAlert): string | null {
  const { entity } = alert
  if (entity.harvest_id) return `/cultivo/cosechas/${entity.harvest_id}`
  if (entity.drying_id) return `/cultivo/secados/${entity.drying_id}`
  if (entity.wet_processing_id) return `/cultivo/beneficios/${entity.wet_processing_id}`
  if (entity.plot_id) return `/cultivo/lotes/${entity.plot_id}`
  if (entity.farm_id) return `/cultivo/fincas/${entity.farm_id}/pagos`
  return null
}
