import { fmtNumber } from '../format'
import { LABOR_ACTIVITY_LABELS } from '../models/labels'
import type { DayLabor, PaymentItem } from '../models/types'

/** Actividad de un jornal: la del catálogo, o la que se escribió si es «otra» */
export const describeActivity = (labor: Pick<DayLabor, 'activity_type' | 'other_detail'>): string =>
  labor.activity_type === 'other' && labor.other_detail
    ? labor.other_detail
    : LABOR_ACTIVITY_LABELS[labor.activity_type]

/** Qué se paga, en una línea: «Recolección · Lote Alto · pasada 2 · 40 kg» */
export function describePaymentItem(item: PaymentItem): string {
  if (item.kind === 'harvest_work') {
    const amount =
      item.payment_type === 'per_kg'
        ? fmtNumber(item.kg_collected, 3, 'kg')
        : `jornal${item.kg_collected !== null ? `, ${fmtNumber(item.kg_collected, 3, 'kg')}` : ''}`
    return `Recolección · ${item.plot_name} · pasada ${item.pass_number} · ${amount}`
  }
  const activity = item.activity_type
    ? describeActivity({ activity_type: item.activity_type, other_detail: item.other_detail })
    : 'Jornal'
  return ['Jornal', activity, item.plot_name].filter(Boolean).join(' · ')
}
