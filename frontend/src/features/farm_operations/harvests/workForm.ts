import { numberOrNull, toInput } from '../components/useFormValues'
import { toKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { todayIso } from '../format'
import type { Harvest, HarvestPaymentType, HarvestWork, HarvestWorkPayload } from '../models/types'

/** Campos del formulario de recolección, como texto */
export interface WorkValues {
  employee_id: string
  work_date: string
  payment_type: string
  kg: string
  rate_per_kg: string
  day_value: string
}

export const emptyWork = (): WorkValues => ({
  employee_id: '',
  work_date: todayIso(),
  payment_type: 'per_kg',
  kg: '',
  rate_per_kg: '',
  day_value: '',
})

export const workValuesFrom = (work: HarvestWork): WorkValues => ({
  employee_id: String(work.employee_id),
  work_date: work.work_date,
  payment_type: work.payment_type,
  kg: toInput(work.kg_collected),
  rate_per_kg: toInput(work.rate_per_kg),
  day_value: toInput(work.day_value),
})

export function workPayload(values: WorkValues, unit: WeightUnit): HarvestWorkPayload {
  const perKg = values.payment_type === 'per_kg'
  return {
    employee_id: Number(values.employee_id),
    work_date: values.work_date,
    payment_type: values.payment_type as HarvestPaymentType,
    kg_collected: toKg(values.kg, unit),
    rate_per_kg: perKg ? numberOrNull(values.rate_per_kg) : null,
    day_value: perKg ? null : numberOrNull(values.day_value),
  }
}

/** Valor a pagar que calculará el servidor, para verlo antes de guardar */
export function estimateValue(values: WorkValues, unit: WeightUnit, harvest: Harvest): number | null {
  if (values.payment_type === 'per_kg') {
    const kg = toKg(values.kg, unit)
    const rate = numberOrNull(values.rate_per_kg) ?? harvest.rate_per_kg
    return kg !== null && rate !== null ? Math.round(kg * rate * 100) / 100 : null
  }
  return numberOrNull(values.day_value) ?? harvest.rate_per_day
}

/** Campos que faltan, con su mensaje; vacío si el formulario está completo */
export function workErrors(values: WorkValues, harvest: Harvest): [keyof WorkValues, string][] {
  const errors: [keyof WorkValues, string][] = []
  if (!values.employee_id) errors.push(['employee_id', 'Elige el recolector'])
  if (!values.work_date) errors.push(['work_date', 'Campo obligatorio'])
  if (values.payment_type === 'per_kg') {
    if (!values.kg.trim()) errors.push(['kg', 'Indica cuánto recogió'])
    if (!values.rate_per_kg.trim() && harvest.rate_per_kg === null) errors.push(['rate_per_kg', 'Indica la tarifa'])
  } else if (!values.day_value.trim() && harvest.rate_per_day === null) {
    errors.push(['day_value', 'Indica el valor del jornal'])
  }
  return errors
}
