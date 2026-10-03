import { DRYING_METHOD_LABELS } from '../models/labels'
import type { Drying } from '../models/types'

/** Método de secado: el del catálogo, o el que se escribió si es «otro» */
export const dryingMethodName = (drying: Pick<Drying, 'method' | 'other_detail'>): string =>
  drying.method === 'other' ? drying.other_detail ?? 'Otro' : DRYING_METHOD_LABELS[drying.method]

/** Composición en una línea: «Lote Alto 60 % · Lote Bajo 40 %» */
export const compositionText = (drying: Pick<Drying, 'composition'>): string =>
  drying.composition.map((plot) => `${plot.plot_name} ${Math.round(plot.share_pct)} %`).join(' · ')
