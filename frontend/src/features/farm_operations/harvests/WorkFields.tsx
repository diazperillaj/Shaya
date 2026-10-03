import { useState } from 'react'
import { createPortal } from 'react-dom'
import { UserPlus } from 'lucide-react'
import { DateField, NumberField, SelectField } from '../components/fields'
import WeightField from '../components/WeightField'
import type { WeightUnit } from '../components/weight'
import EmployeeFormDialog from '../employees/EmployeeFormDialog'
import { fmtMoney, todayIso } from '../format'
import { HARVEST_PAYMENT_LABELS } from '../models/labels'
import type { Employee, Harvest, HarvestPaymentType } from '../models/types'
import type { WorkValues } from './workForm'
import { estimateValue } from './workForm'

/** Lo mínimo de un empleado para elegirlo */
export type EmployeeOption = Pick<Employee, 'id' | 'full_name'>

type Bind = (field: keyof WorkValues) => { value: string; error?: string; onChange: (value: string) => void }

/**
 * Campos de la recolección de un día: quién, cuándo, cómo se paga, cuánto
 * recogió y el valor que resulta con las tarifas de la cosecha.
 */
export default function WorkFields({
  harvest,
  employees,
  values,
  bind,
  unit,
  onUnitChange,
  onEmployeeCreated,
}: {
  harvest: Harvest
  /** Empleados que pueden recibir recolección (activos, más el del registro que se corrige) */
  employees: EmployeeOption[]
  values: WorkValues
  bind: Bind
  unit: WeightUnit
  onUnitChange: (unit: WeightUnit) => void
  onEmployeeCreated: (employee: Employee) => void
}) {
  const [addingEmployee, setAddingEmployee] = useState(false)
  const perKg = values.payment_type === 'per_kg'
  const estimate = estimateValue(values, unit, harvest)
  const kgField = bind('kg')

  return (
    <>
      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <SelectField
          label="Recolector"
          required
          placeholder="Elige el empleado"
          options={employees.map((employee) => ({ value: String(employee.id), label: employee.full_name }))}
          {...bind('employee_id')}
        />
        <button
          type="button"
          onClick={() => setAddingEmployee(true)}
          className="flex w-fit items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-50"
        >
          <UserPlus className="h-3.5 w-3.5" /> Nuevo recolector
        </button>
      </div>

      <DateField label="Fecha" required max={todayIso()} {...bind('work_date')} />
      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-gray-700">Forma de pago</span>
        <div className="grid grid-cols-2 gap-1 rounded-xl bg-gray-100 p-1" role="radiogroup">
          {(Object.keys(HARVEST_PAYMENT_LABELS) as HarvestPaymentType[]).map((option) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={values.payment_type === option}
              onClick={() => bind('payment_type').onChange(option)}
              className={`rounded-lg px-2 py-1.5 text-sm font-medium transition ${
                values.payment_type === option ? 'bg-white text-emerald-900 shadow-sm' : 'text-gray-500'
              }`}
            >
              {HARVEST_PAYMENT_LABELS[option]}
            </button>
          ))}
        </div>
      </div>

      <WeightField
        label={perKg ? 'Café recogido' : 'Café recogido (opcional)'}
        required={perKg}
        hint={perKg ? undefined : 'Si se pesó, suma al total de la cosecha.'}
        value={kgField.value}
        error={kgField.error}
        onChange={kgField.onChange}
        unit={unit}
        onUnitChange={onUnitChange}
      />
      {perKg ? (
        <NumberField
          label="Tarifa por kg"
          unit="COP"
          min="0"
          placeholder={harvest.rate_per_kg !== null ? String(harvest.rate_per_kg) : undefined}
          hint={harvest.rate_per_kg !== null ? 'Vacío = la tarifa de la cosecha.' : 'La cosecha no tiene tarifa por defecto.'}
          {...bind('rate_per_kg')}
        />
      ) : (
        <NumberField
          label="Valor del jornal"
          unit="COP"
          min="0"
          placeholder={harvest.rate_per_day !== null ? String(harvest.rate_per_day) : undefined}
          hint={harvest.rate_per_day !== null ? 'Vacío = el jornal de la cosecha.' : 'La cosecha no tiene jornal por defecto.'}
          {...bind('day_value')}
        />
      )}

      <p className="text-sm text-gray-600 sm:col-span-2">
        Valor a pagar: <span className="font-semibold text-gray-900">{fmtMoney(estimate)}</span>
      </p>

      {/* Fuera del formulario de la recolección: un formulario no puede ir dentro de otro */}
      {addingEmployee &&
        createPortal(
          <EmployeeFormDialog
            farmId={harvest.farm_id}
            onClose={() => setAddingEmployee(false)}
            onSaved={(employee) => {
              setAddingEmployee(false)
              if (employee) onEmployeeCreated(employee)
            }}
          />,
          document.body,
        )}
    </>
  )
}
