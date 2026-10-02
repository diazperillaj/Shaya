import type { LucideIcon } from 'lucide-react'
import { Bug, Droplets, Flower2, Leaf, Scissors, SprayCan } from 'lucide-react'
import { numberOrNull, textOrNull, toInput } from '../components/useFormValues'
import { fmtMoney, fmtNumber } from '../format'
import {
  CULTURAL_PRACTICE_LABELS,
  FERTILIZATION_METHOD_LABELS,
  INTENSITY_LABELS,
  SEVERITY_LABELS,
} from '../models/labels'
import type { AnyLabor, LaborKind, LaborPayload, SupplyType } from '../models/types'

/**
 * Lo que distingue a cada labor en pantalla: nombres, ícono, fecha, montos
 * que se reparten entre lotes y cómo se arma su cuerpo para la API.
 */

/** Montos propios de cada lote: en el registro múltiple se reparten por área */
export type AmountField = 'quantity' | 'cost' | 'volume_liters'

export interface AmountInfo {
  field: AmountField
  label: string
  /** Unidad fija; sin ella se usa la del insumo */
  unit?: string
  decimals: number
  step: string
  required: boolean
}

const QUANTITY: AmountInfo = { field: 'quantity', label: 'Cantidad', decimals: 3, step: '0.001', required: true }
const COST: AmountInfo = { field: 'cost', label: 'Costo', unit: 'COP', decimals: 0, step: '1', required: false }
const VOLUME: AmountInfo = { field: 'volume_liters', label: 'Volumen', unit: 'L', decimals: 1, step: '0.1', required: false }

export interface LaborInfo {
  label: string
  plural: string
  icon: LucideIcon
  /** Ayuda corta en el selector de labores */
  hint: string
  /** Campo de fecha en la API */
  dateField: string
  dateLabel: string
  amounts: AmountInfo[]
  /** Se puede registrar en varios lotes a la vez */
  bulk: boolean
  /** Tipos de insumo que se listan primero, en las labores con insumo */
  supplyTypes?: SupplyType[]
}

export const LABOR_INFO: Record<LaborKind, LaborInfo> = {
  fertilizations: {
    label: 'Fertilización',
    plural: 'Fertilizaciones',
    icon: Leaf,
    hint: 'Abono al suelo o foliar',
    dateField: 'application_date',
    dateLabel: 'Fecha de aplicación',
    amounts: [QUANTITY, COST],
    bulk: true,
    supplyTypes: ['fertilizer', 'amendment'],
  },
  'phytosanitary-apps': {
    label: 'Aplicación fitosanitaria',
    plural: 'Fitosanitarios',
    icon: SprayCan,
    hint: 'Control de plagas, enfermedades o malezas',
    dateField: 'application_date',
    dateLabel: 'Fecha de aplicación',
    amounts: [QUANTITY, COST],
    bulk: true,
    supplyTypes: ['phytosanitary', 'herbicide'],
  },
  irrigations: {
    label: 'Riego',
    plural: 'Riegos',
    icon: Droplets,
    hint: 'Método, duración y volumen',
    dateField: 'irrigation_date',
    dateLabel: 'Fecha del riego',
    amounts: [VOLUME],
    bulk: true,
  },
  'pest-monitorings': {
    label: 'Monitoreo de plagas',
    plural: 'Monitoreos',
    icon: Bug,
    hint: '% de broca, roya u otra plaga',
    dateField: 'monitoring_date',
    dateLabel: 'Fecha del muestreo',
    amounts: [],
    bulk: false,
  },
  'cultural-practices': {
    label: 'Labor cultural',
    plural: 'Labores culturales',
    icon: Scissors,
    hint: 'Deshierba, poda, sombrío, encalado',
    dateField: 'practice_date',
    dateLabel: 'Fecha de la labor',
    amounts: [COST],
    bulk: true,
  },
  'flowering-records': {
    label: 'Floración',
    plural: 'Floraciones',
    icon: Flower2,
    hint: 'Para estimar la cosecha',
    dateField: 'flowering_date',
    dateLabel: 'Fecha de floración',
    amounts: [],
    bulk: true,
  },
}

export const LABOR_KINDS = Object.keys(LABOR_INFO) as LaborKind[]

/** Campos del formulario de labor (la unión de todas; cada labor usa los suyos) */
export const EMPTY_VALUES = {
  date: '',
  supply_id: '',
  method: 'soil',
  dose_per_tree_g: '',
  target: '',
  dose_description: '',
  irrigation_method: '',
  duration_minutes: '',
  practice_type: 'weeding',
  other_detail: '',
  intensity: 'high',
  broca_pct: '',
  roya_pct: '',
  other_pest: '',
  other_pest_pct: '',
  severity: '',
  observations: '',
  quantity: '',
  cost: '',
  volume_liters: '',
}

export type LaborValues = typeof EMPTY_VALUES
export type LaborField = keyof LaborValues

/** Fecha de un registro, sea cual sea su labor */
export const laborDate = (labor: AnyLabor): string =>
  (labor.record as unknown as Record<string, string>)[LABOR_INFO[labor.kind].dateField]

/** Valores del formulario para corregir un registro */
export function valuesFromRecord(labor: AnyLabor): LaborValues {
  const base = { ...EMPTY_VALUES, date: laborDate(labor), observations: toInput(labor.record.observations) }
  switch (labor.kind) {
    case 'fertilizations': {
      const r = labor.record
      return {
        ...base,
        supply_id: String(r.supply_id),
        method: r.method,
        dose_per_tree_g: toInput(r.dose_per_tree_g),
        quantity: toInput(r.quantity),
        cost: toInput(r.cost),
      }
    }
    case 'phytosanitary-apps': {
      const r = labor.record
      return {
        ...base,
        supply_id: String(r.supply_id),
        target: r.target,
        dose_description: toInput(r.dose_description),
        quantity: toInput(r.quantity),
        cost: toInput(r.cost),
      }
    }
    case 'irrigations': {
      const r = labor.record
      return {
        ...base,
        irrigation_method: toInput(r.method),
        duration_minutes: toInput(r.duration_minutes),
        volume_liters: toInput(r.volume_liters),
      }
    }
    case 'pest-monitorings': {
      const r = labor.record
      return {
        ...base,
        broca_pct: toInput(r.broca_pct),
        roya_pct: toInput(r.roya_pct),
        other_pest: toInput(r.other_pest),
        other_pest_pct: toInput(r.other_pest_pct),
        severity: toInput(r.severity),
      }
    }
    case 'cultural-practices': {
      const r = labor.record
      return { ...base, practice_type: r.practice_type, other_detail: toInput(r.other_detail), cost: toInput(r.cost) }
    }
    case 'flowering-records':
      return { ...base, intensity: labor.record.intensity }
  }
}

/** Campos comunes de la labor (todo menos los montos de cada lote) */
export function sharedPayload(kind: LaborKind, values: LaborValues): LaborPayload {
  const observations = textOrNull(values.observations)
  switch (kind) {
    case 'fertilizations':
      return {
        supply_id: Number(values.supply_id),
        application_date: values.date,
        method: values.method,
        dose_per_tree_g: numberOrNull(values.dose_per_tree_g),
        observations,
      }
    case 'phytosanitary-apps':
      return {
        supply_id: Number(values.supply_id),
        application_date: values.date,
        target: values.target.trim(),
        dose_description: textOrNull(values.dose_description),
        observations,
      }
    case 'irrigations':
      return {
        irrigation_date: values.date,
        method: textOrNull(values.irrigation_method),
        duration_minutes: numberOrNull(values.duration_minutes),
        observations,
      }
    case 'pest-monitorings':
      return {
        monitoring_date: values.date,
        broca_pct: numberOrNull(values.broca_pct),
        roya_pct: numberOrNull(values.roya_pct),
        other_pest: textOrNull(values.other_pest),
        other_pest_pct: numberOrNull(values.other_pest_pct),
        severity: values.severity || null,
        observations,
      }
    case 'cultural-practices':
      return {
        practice_type: values.practice_type,
        other_detail: values.practice_type === 'other' ? textOrNull(values.other_detail) : null,
        practice_date: values.date,
        observations,
      }
    case 'flowering-records':
      return { flowering_date: values.date, intensity: values.intensity, observations }
  }
}

/** Montos de un lote, como texto del formulario → valores de la API */
export const amountsPayload = (kind: LaborKind, amounts: Partial<Record<AmountField, string>>): LaborPayload =>
  Object.fromEntries(
    LABOR_INFO[kind].amounts.map(({ field }) => [field, numberOrNull(amounts[field] ?? '')]),
  )

/** Resumen de una labor en una línea, para el historial */
export function describeLabor(labor: AnyLabor): { title: string; detail: string } {
  const join = (...parts: (string | null | false)[]) => parts.filter(Boolean).join(' · ')
  const money = (value: number | null) => value !== null && fmtMoney(value)

  switch (labor.kind) {
    case 'fertilizations': {
      const r = labor.record
      return {
        title: `Fertilización · ${r.supply.name}`,
        detail: join(fmtNumber(r.quantity, 3, r.supply.unit), FERTILIZATION_METHOD_LABELS[r.method], money(r.cost)),
      }
    }
    case 'phytosanitary-apps': {
      const r = labor.record
      return {
        title: `Fitosanitario · ${r.target}`,
        detail: join(r.supply.name, fmtNumber(r.quantity, 3, r.supply.unit), r.dose_description, money(r.cost)),
      }
    }
    case 'irrigations': {
      const r = labor.record
      return {
        title: 'Riego',
        detail: join(
          r.method,
          r.duration_minutes !== null && fmtNumber(r.duration_minutes, 0, 'min'),
          r.volume_liters !== null && fmtNumber(r.volume_liters, 1, 'L'),
        ) || 'Sin detalle',
      }
    }
    case 'pest-monitorings': {
      const r = labor.record
      return {
        title: 'Monitoreo de plagas',
        detail: join(
          r.broca_pct !== null && `Broca ${fmtNumber(r.broca_pct, 2, '%')}`,
          r.roya_pct !== null && `Roya ${fmtNumber(r.roya_pct, 2, '%')}`,
          r.other_pest && `${r.other_pest}${r.other_pest_pct !== null ? ` ${fmtNumber(r.other_pest_pct, 2, '%')}` : ''}`,
          r.severity && `Severidad ${SEVERITY_LABELS[r.severity].toLowerCase()}`,
        ),
      }
    }
    case 'cultural-practices': {
      const r = labor.record
      const name = r.practice_type === 'other' && r.other_detail ? r.other_detail : CULTURAL_PRACTICE_LABELS[r.practice_type]
      return { title: name, detail: join(money(r.cost)) || 'Labor cultural' }
    }
    case 'flowering-records':
      return { title: 'Floración', detail: `Intensidad ${INTENSITY_LABELS[labor.record.intensity].toLowerCase()}` }
  }
}
