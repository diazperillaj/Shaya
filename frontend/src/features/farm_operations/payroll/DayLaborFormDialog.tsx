import { HardHat } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, SelectField, TextAreaField, TextField } from '../components/fields'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import { LABOR_ACTIVITY_LABELS } from '../models/labels'
import type { DayLabor, Employee, LaborActivity, Plot } from '../models/types'
import { createDayLabor, deleteDayLabor, updateDayLabor } from '../services/payroll.api'

/** Registrar o corregir un jornal (sin pagar) de un trabajador de la finca */
export default function DayLaborFormDialog({
  employees,
  plots,
  labor,
  suggestedValue,
  onClose,
  onSaved,
}: {
  /** Empleados activos de la finca */
  employees: Employee[]
  /** Lotes activos de la finca */
  plots: Plot[]
  labor?: DayLabor
  /** Valor del último jornal registrado, para no escribirlo cada vez */
  suggestedValue?: number
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, requireFields } = useFormValues({
    employee_id: toInput(labor?.employee_id),
    labor_date: labor?.labor_date ?? todayIso(),
    activity_type: labor?.activity_type ?? 'weeding',
    other_detail: labor?.other_detail ?? '',
    plot_id: toInput(labor?.plot_id),
    daily_value: toInput(labor?.daily_value ?? suggestedValue),
    observations: labor?.observations ?? '',
  })
  const isOther = values.activity_type === 'other'

  // Un jornal viejo puede ser de un empleado inactivo o de un lote cerrado
  const employeeOptions = employees.map((employee) => ({ value: String(employee.id), label: employee.full_name }))
  if (labor && !employees.some((employee) => employee.id === labor.employee_id)) {
    employeeOptions.push({ value: String(labor.employee_id), label: labor.employee_name })
  }
  const plotOptions = plots.map((plot) => ({ value: String(plot.id), label: plot.name }))
  if (labor?.plot_id && !plots.some((plot) => plot.id === labor.plot_id)) {
    plotOptions.push({ value: String(labor.plot_id), label: labor.plot_name ?? 'Lote cerrado' })
  }

  const handleSubmit = async () => {
    const required = ['employee_id', 'labor_date', 'daily_value'] as const
    if (!requireFields(isOther ? [...required, 'other_detail'] : [...required])) return
    const payload = {
      employee_id: Number(values.employee_id),
      labor_date: values.labor_date,
      activity_type: values.activity_type as LaborActivity,
      other_detail: isOther ? textOrNull(values.other_detail) : null,
      plot_id: values.plot_id ? Number(values.plot_id) : null,
      daily_value: numberOrNull(values.daily_value) ?? 0,
      observations: textOrNull(values.observations),
    }
    if (labor) await updateDayLabor(labor.id, payload)
    else await createDayLabor(payload)
    onSaved()
  }

  return (
    <FormDialog
      title={labor ? 'Corregir jornal' : 'Registrar jornal'}
      description="Un día de trabajo pagado que no es recolección."
      icon={HardHat}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        labor
          ? {
              label: 'Eliminar',
              confirm: `¿Eliminar el jornal de ${labor.employee_name}?`,
              onConfirm: async () => {
                await deleteDayLabor(labor.id)
                onSaved()
              },
            }
          : undefined
      }
    >
      <FormSection>
        <SelectField label="Trabajador" required placeholder="Elige el empleado" options={employeeOptions} {...bind('employee_id')} />
        <DateField label="Fecha" required max={todayIso()} {...bind('labor_date')} />
        <SelectField
          label="Actividad"
          required
          options={Object.entries(LABOR_ACTIVITY_LABELS).map(([value, label]) => ({ value, label }))}
          {...bind('activity_type')}
        />
        {isOther && <TextField label="¿Cuál actividad?" required {...bind('other_detail')} />}
        <SelectField label="Lote" placeholder="Sin lote específico" options={plotOptions} {...bind('plot_id')} />
        <NumberField label="Valor del jornal" required unit="COP" min="0" {...bind('daily_value')} />
        <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
