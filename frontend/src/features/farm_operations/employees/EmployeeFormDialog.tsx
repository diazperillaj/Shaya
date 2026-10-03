import { UserRound } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { FormSection, TextAreaField, TextField } from '../components/fields'
import { textOrNull, useFormValues } from '../components/useFormValues'
import type { Employee } from '../models/types'
import { createEmployee, deleteEmployee, updateEmployee } from '../services/employees.api'

/**
 * Crear o editar un trabajador de la finca.
 *
 * No exige documento: los recolectores suelen ser informales.
 */
export default function EmployeeFormDialog({
  farmId,
  employee,
  onClose,
  onSaved,
}: {
  farmId: number
  employee?: Employee
  onClose: () => void
  /** Recibe el empleado guardado (nada si se eliminó) */
  onSaved: (employee?: Employee) => void
}) {
  const { values, bind, requireFields } = useFormValues({
    full_name: employee?.full_name ?? '',
    document: employee?.document ?? '',
    phone: employee?.phone ?? '',
    observations: employee?.observations ?? '',
  })

  const handleSubmit = async () => {
    if (!requireFields(['full_name'])) return
    const payload = {
      full_name: values.full_name.trim(),
      document: textOrNull(values.document),
      phone: textOrNull(values.phone),
      observations: textOrNull(values.observations),
    }
    onSaved(employee ? await updateEmployee(employee.id, payload) : await createEmployee(farmId, payload))
  }

  return (
    <FormDialog
      title={employee ? 'Editar empleado' : 'Agregar empleado'}
      icon={UserRound}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        employee
          ? {
              label: 'Eliminar',
              confirm: `¿Eliminar a ${employee.full_name}? Si ya tiene pagos registrados, desactívalo en su lugar.`,
              onConfirm: async () => {
                await deleteEmployee(employee.id)
                onSaved()
              },
            }
          : undefined
      }
    >
      <FormSection>
        <TextField label="Nombre completo" required wide {...bind('full_name')} />
        <TextField label="Documento" {...bind('document')} />
        <TextField label="Teléfono" type="tel" {...bind('phone')} />
        <TextAreaField label="Observaciones" {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
