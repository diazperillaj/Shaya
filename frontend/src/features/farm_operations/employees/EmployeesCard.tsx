import { useCallback, useState } from 'react'
import { Pencil, UserPlus } from 'lucide-react'
import { Badge, Button, Card, ErrorMessage, Pager } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { usePagination } from '../components/usePagination'
import type { Employee } from '../models/types'
import { fetchEmployees, setEmployeeActive } from '../services/employees.api'
import EmployeeFormDialog from './EmployeeFormDialog'

/**
 * Trabajadores de una finca. Un empleado con historial se desactiva en
 * lugar de borrarse.
 */
export default function EmployeesCard({ farmId }: { farmId: number }) {
  const load = useCallback(() => fetchEmployees(farmId), [farmId])
  const { data: employees, error, reload } = useLoader(load)
  const shown = usePagination(employees)

  const [dialog, setDialog] = useState<{ employee?: Employee } | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const toggleActive = async (employee: Employee) => {
    setActionError(null)
    try {
      await setEmployeeActive(employee.id, !employee.active)
      reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Error actualizando el empleado')
    }
  }

  return (
    <Card
      title="Empleados"
      actions={
        <Button icon={UserPlus} onClick={() => setDialog({})}>
          Agregar
        </Button>
      }
    >
      {(error || actionError) && <ErrorMessage message={(error ?? actionError) as string} />}

      {employees && employees.length === 0 && (
        <p className="text-sm text-gray-400">
          Registra a los trabajadores para llevar después la recolección y los jornales.
        </p>
      )}

      {employees && employees.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {shown.visible.map((employee) => (
            <li key={employee.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
              <div className={employee.active ? '' : 'opacity-60'}>
                <p className="flex items-center gap-2 text-sm font-medium text-gray-900">
                  {employee.full_name}
                  {!employee.active && <Badge>Inactivo</Badge>}
                </p>
                <p className="text-xs text-gray-400">
                  {[employee.document, employee.phone].filter(Boolean).join(' · ') || 'Sin documento ni teléfono'}
                </p>
              </div>
              <div className="flex gap-1">
                <button
                  type="button"
                  onClick={() => toggleActive(employee)}
                  className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100"
                >
                  {employee.active ? 'Desactivar' : 'Activar'}
                </button>
                <button
                  type="button"
                  onClick={() => setDialog({ employee })}
                  aria-label={`Editar a ${employee.full_name}`}
                  className="rounded-lg p-1.5 text-gray-500 hover:bg-gray-100 hover:text-emerald-800"
                >
                  <Pencil className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
      <Pager state={shown} />

      {dialog && (
        <EmployeeFormDialog
          farmId={farmId}
          employee={dialog.employee}
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
