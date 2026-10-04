import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BellRing, CheckCircle2, ChevronRight, ListChecks } from 'lucide-react'
import { Card } from '../components/ui'
import { fmtDate } from '../format'
import type { AlertSeverity, FarmAlert } from '../models/types'
import { ALERT_LABELS, alertLink, SEVERITY_INFO } from './alertInfo'

const VISIBLE = 6

function AlertItem({ alert, showFarm }: { alert: FarmAlert; showFarm: boolean }) {
  const link = alertLink(alert)
  const body = (
    <>
      <span className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${SEVERITY_INFO[alert.severity].dot}`} />
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-medium text-gray-900">
          {ALERT_LABELS[alert.type] ?? alert.type}
          {showFarm && <span className="font-normal text-gray-400"> · {alert.farm_name}</span>}
        </span>
        <span className="block text-sm text-gray-600">{alert.message}</span>
        {alert.since && <span className="block text-xs text-gray-400">Desde el {fmtDate(alert.since)}</span>}
      </span>
      {link && <ChevronRight className="mt-1 h-4 w-4 flex-shrink-0 text-gray-300" />}
    </>
  )
  return (
    <li>
      {link ? (
        <Link to={link} className="-mx-2 flex items-start gap-2.5 rounded-xl px-2 py-2 transition hover:bg-gray-50">
          {body}
        </Link>
      ) : (
        <div className="flex items-start gap-2.5 py-2">{body}</div>
      )}
    </li>
  )
}

function AlertGroup({ severity, alerts, showFarm }: { severity: AlertSeverity; alerts: FarmAlert[]; showFarm: boolean }) {
  const [expanded, setExpanded] = useState(false)
  if (alerts.length === 0) return null
  const visible = expanded ? alerts : alerts.slice(0, VISIBLE)
  return (
    <div>
      <p className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        {SEVERITY_INFO[severity].plural}
        <span className={`rounded-full border px-2 py-0.5 text-[11px] normal-case ${SEVERITY_INFO[severity].badge}`}>
          {alerts.length}
        </span>
      </p>
      <ul className="divide-y divide-gray-50">
        {visible.map((alert, index) => (
          <AlertItem key={`${alert.type}-${index}`} alert={alert} showFarm={showFarm} />
        ))}
      </ul>
      {alerts.length > VISIBLE && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="mt-1 text-xs font-medium text-emerald-800 hover:underline"
        >
          {expanded ? 'Ver menos' : `Ver las ${alerts.length}`}
        </button>
      )}
    </div>
  )
}

/** Riesgos y desvíos activos, agrupados por severidad; cada uno enlaza a su entidad */
export function AlertsPanel({ alerts, showFarm }: { alerts: FarmAlert[]; showFarm: boolean }) {
  const high = alerts.filter((a) => a.severity === 'high')
  const medium = alerts.filter((a) => a.severity === 'medium')
  return (
    <Card title="Alertas">
      {high.length + medium.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-gray-500">
          <CheckCircle2 className="h-4 w-4 text-emerald-700" /> Sin riesgos ni desvíos activos.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          <AlertGroup severity="high" alerts={high} showFarm={showFarm} />
          <AlertGroup severity="medium" alerts={medium} showFarm={showFarm} />
        </div>
      )}
      <p className="mt-3 flex items-center gap-1.5 text-xs text-gray-400">
        <BellRing className="h-3.5 w-3.5" /> Las alertas informan: ninguna bloquea una operación.
      </p>
    </Card>
  )
}

/** Recordatorios de labores como lista de chequeo: solo informan (§3.4) */
export function RemindersCard({ alerts, showFarm }: { alerts: FarmAlert[]; showFarm: boolean }) {
  const reminders = alerts.filter((a) => a.severity === 'info')
  return (
    <Card title="Recordatorios de labores">
      {reminders.length === 0 ? (
        <p className="flex items-center gap-2 text-sm text-gray-500">
          <ListChecks className="h-4 w-4 text-emerald-700" /> Las labores están al día.
        </p>
      ) : (
        <AlertGroup severity="info" alerts={reminders} showFarm={showFarm} />
      )}
    </Card>
  )
}
