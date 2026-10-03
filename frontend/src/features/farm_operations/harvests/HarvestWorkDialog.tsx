import { useState } from 'react'
import { Weight } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { FormSection } from '../components/fields'
import { useFormValues } from '../components/useFormValues'
import type { WeightUnit } from '../components/weight'
import type { Employee, Harvest, HarvestWork } from '../models/types'
import { deleteHarvestWork, updateHarvestWork } from '../services/harvests.api'
import WorkFields from './WorkFields'
import type { EmployeeOption } from './WorkFields'
import { workErrors, workPayload, workValuesFrom } from './workForm'
import type { WorkValues } from './workForm'

/** Corregir o eliminar la recolección de un día (sin pagar, con la cosecha abierta) */
export default function HarvestWorkDialog({
  harvest,
  work,
  employees,
  onClose,
  onSaved,
}: {
  harvest: Harvest
  work: HarvestWork
  employees: EmployeeOption[]
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, setFieldError } = useFormValues<keyof WorkValues>(workValuesFrom(work))
  const [unit, setUnit] = useState<WeightUnit>('kg')
  const [extraEmployees, setExtraEmployees] = useState<Employee[]>([])

  const handleSubmit = async () => {
    const errors = workErrors(values, harvest)
    errors.forEach(([field, message]) => setFieldError(field, message))
    if (errors.length > 0) return
    await updateHarvestWork(work.id, workPayload(values, unit))
    onSaved()
  }

  return (
    <FormDialog
      title="Corregir recolección"
      description={`${work.employee_name} · pasada ${harvest.pass_number} del lote «${harvest.plot_name}»`}
      icon={Weight}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={{
        label: 'Eliminar',
        confirm: `¿Eliminar la recolección de ${work.employee_name}?`,
        onConfirm: async () => {
          await deleteHarvestWork(work.id)
          onSaved()
        },
      }}
    >
      <FormSection>
        <WorkFields
          harvest={harvest}
          employees={[...employees, ...extraEmployees]}
          values={values}
          bind={bind}
          unit={unit}
          onUnitChange={setUnit}
          onEmployeeCreated={(employee) => {
            setExtraEmployees((current) => [...current, employee])
            bind('employee_id').onChange(String(employee.id))
          }}
        />
      </FormSection>
    </FormDialog>
  )
}
