import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { HardHat, Wallet } from 'lucide-react'
import { Badge, Button, Card, ErrorMessage } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtMoney } from '../format'
import type { DayLabor, Plot } from '../models/types'
import { fetchEmployees } from '../services/employees.api'
import { fetchDayLabors } from '../services/payroll.api'
import DayLaborFormDialog from './DayLaborFormDialog'
import { describeActivity } from './describe'

const VISIBLE = 8

/** Jornales recientes de la finca y acceso a los pagos */
export default function DayLaborsCard({ farmId, plots }: { farmId: number; plots: Plot[] }) {
  const navigate = useNavigate()
  const loadLabors = useCallback(() => fetchDayLabors(farmId), [farmId])
  const loadEmployees = useCallback(() => fetchEmployees(farmId), [farmId])
  const { data: labors, error, reload } = useLoader(loadLabors)
  const { data: employees } = useLoader(loadEmployees)
  const [dialog, setDialog] = useState<{ labor?: DayLabor } | null>(null)
  const [showAll, setShowAll] = useState(false)

  const active = (employees ?? []).filter((employee) => employee.active)
  const visible = showAll ? labors ?? [] : (labors ?? []).slice(0, VISIBLE)

  return (
    <Card
      title="Jornales"
      actions={
        <>
          <Button icon={Wallet} onClick={() => navigate(`/cultivo/fincas/${farmId}/pagos`)}>Pagos</Button>
          <Button icon={HardHat} onClick={() => setDialog({})} disabled={active.length === 0}>Registrar jornal</Button>
        </>
      }
    >
      {error && <ErrorMessage message={error} />}
      {employees && active.length === 0 && (
        <p className="mb-2 text-sm text-gray-400">Agrega primero a los trabajadores de la finca.</p>
      )}
      {labors && labors.length === 0 && active.length > 0 && (
        <p className="text-sm text-gray-400">Sin jornales registrados: deshierbas, podas, fumigaciones pagadas por día…</p>
      )}
      {visible.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {visible.map((labor) => (
            <li key={labor.id}>
              <button
                type="button"
                disabled={labor.paid}
                onClick={() => setDialog({ labor })}
                className="-mx-2 flex w-[calc(100%+1rem)] items-center justify-between gap-3 rounded-xl px-2 py-2.5 text-left enabled:hover:bg-gray-50"
              >
                <span>
                  <span className="block text-sm text-gray-900">
                    {labor.employee_name} · {describeActivity(labor)}
                  </span>
                  <span className="block text-xs text-gray-400">
                    {fmtDate(labor.labor_date)}
                    {labor.plot_name && ` · ${labor.plot_name}`}
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900">{fmtMoney(labor.daily_value)}</span>
                  <Badge tone={labor.paid ? 'green' : 'amber'}>{labor.paid ? 'Pagado' : 'Pendiente'}</Badge>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {labors && labors.length > VISIBLE && (
        <button
          type="button"
          onClick={() => setShowAll((current) => !current)}
          className="mt-2 text-sm font-medium text-gray-500 hover:text-emerald-800"
        >
          {showAll ? 'Ver menos' : `Ver los ${labors.length} jornales`}
        </button>
      )}

      {dialog && (
        <DayLaborFormDialog
          employees={active}
          plots={plots}
          labor={dialog.labor}
          suggestedValue={labors?.[0]?.daily_value}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            reload()
          }}
        />
      )}
    </Card>
  )
}
