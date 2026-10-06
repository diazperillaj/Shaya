import { Link } from 'react-router-dom'
import { BellRing, CheckCircle2, ChevronRight, ListChecks } from 'lucide-react'
import { Card, Pager } from '../components/ui'
import { usePagination } from '../components/usePagination'
import { fmtDate } from '../format'
import type { AlertSeverity, FarmAlert } from '../models/types'
import { ALERT_LABELS, alertLink, SEVERITY_INFO } from './alertInfo'

/** Cuántas alertas hay de una severidad, como etiqueta del encabezado */
function Count({ severity, count }: { severity: AlertSeverity; count: number }) {
  return (
    <span className={`flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${SEVERITY_INFO[severity].badge}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${SEVERITY_INFO[severity].dot}`} />
      {SEVERITY_INFO[severity].plural} {count}
    </span>
  )
}

/**
 * Tabla de alertas a todo el ancho, de a 10 por página. Cada fila lleva a la
 * entidad que hay que revisar (cosecha, secado, beneficio, lote o pagos).
 */
function AlertsTable({ alerts, showFarm, withSeverity }: { alerts: FarmAlert[]; showFarm: boolean; withSeverity: boolean }) {
  const shown = usePagination(alerts)
  return (
    <>
      <div className="-mx-5 overflow-x-auto px-5">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-left text-xs uppercase tracking-wide text-gray-400">
              {withSeverity && <th className="w-px py-2 pr-3 font-medium">Nivel</th>}
              <th className="py-2 pr-3 font-medium">Tipo</th>
              {showFarm && <th className="py-2 pr-3 font-medium">Finca</th>}
              <th className="py-2 pr-3 font-medium">Detalle</th>
              <th className="w-px whitespace-nowrap py-2 pr-3 font-medium">Desde</th>
              <th className="w-px py-2" aria-label="Abrir" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {shown.visible.map((alert, index) => {
              const link = alertLink(alert)
              const label = ALERT_LABELS[alert.type] ?? alert.type
              return (
                <tr key={`${alert.type}-${alert.farm_id}-${index}`} className="transition-colors duration-150 hover:bg-gray-50">
                  {withSeverity && (
                    <td className="py-2.5 pr-3 align-top">
                      <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium ${SEVERITY_INFO[alert.severity].badge}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${SEVERITY_INFO[alert.severity].dot}`} />
                        {SEVERITY_INFO[alert.severity].label}
                      </span>
                    </td>
                  )}
                  <td className="whitespace-nowrap py-2.5 pr-3 align-top font-medium text-gray-900">
                    {link ? (
                      <Link to={link} className="rounded hover:text-emerald-800">{label}</Link>
                    ) : (
                      label
                    )}
                  </td>
                  {showFarm && <td className="whitespace-nowrap py-2.5 pr-3 align-top text-gray-600">{alert.farm_name}</td>}
                  <td className="py-2.5 pr-3 align-top text-gray-600">{alert.message}</td>
                  <td className="whitespace-nowrap py-2.5 pr-3 align-top text-xs text-gray-400">
                    {alert.since ? fmtDate(alert.since) : '—'}
                  </td>
                  <td className="py-2.5 align-top">
                    {link && (
                      <Link
                        to={link}
                        aria-label={`Abrir: ${label}`}
                        className="flex h-6 w-6 items-center justify-center rounded-lg text-gray-400 transition-colors duration-150 hover:bg-emerald-50 hover:text-emerald-800"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <Pager state={shown} />
    </>
  )
}

/** Riesgos y desvíos activos, a todo el ancho; cada uno enlaza a su entidad */
export function AlertsPanel({ alerts, showFarm }: { alerts: FarmAlert[]; showFarm: boolean }) {
  const high = alerts.filter((a) => a.severity === 'high')
  const medium = alerts.filter((a) => a.severity === 'medium')
  return (
    <Card
      title="Alertas"
      actions={
        high.length + medium.length > 0 && (
          <>
            <Count severity="high" count={high.length} />
            <Count severity="medium" count={medium.length} />
          </>
        )
      }
    >
      {high.length + medium.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-gray-500">
          <CheckCircle2 className="h-4 w-4 text-emerald-700" /> Sin riesgos ni desvíos activos.
        </p>
      ) : (
        <AlertsTable alerts={[...high, ...medium]} showFarm={showFarm} withSeverity />
      )}
      <p className="mt-3 flex items-center gap-1.5 text-xs text-gray-400">
        <BellRing className="h-3.5 w-3.5" /> Las alertas informan: ninguna bloquea una operación.
      </p>
    </Card>
  )
}

/** Recordatorios de labores a todo el ancho: solo informan (§3.4) */
export function RemindersCard({ alerts, showFarm }: { alerts: FarmAlert[]; showFarm: boolean }) {
  const reminders = alerts.filter((a) => a.severity === 'info')
  return (
    <Card
      title="Recordatorios de labores"
      actions={reminders.length > 0 && <Count severity="info" count={reminders.length} />}
    >
      {reminders.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-gray-500">
          <ListChecks className="h-4 w-4 text-emerald-700" /> Las labores están al día.
        </p>
      ) : (
        <AlertsTable alerts={reminders} showFarm={showFarm} withSeverity={false} />
      )}
    </Card>
  )
}
