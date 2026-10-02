import { Archive, RotateCcw } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, TextAreaField } from '../components/fields'
import { textOrNull, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import type { Plot } from '../models/types'
import { closePlot, reopenPlot } from '../services/plots.api'

/**
 * Cerrar un lote (definitivo, cuando deja de dar cosecha) o reabrirlo
 * (solo para corregir un cierre hecho por error).
 */
export default function PlotStatusDialog({
  plot,
  onClose,
  onSaved,
}: {
  plot: Plot
  onClose: () => void
  onSaved: (plot: Plot) => void
}) {
  const closing = plot.status === 'active'
  const { values, bind, requireFields } = useFormValues({
    closed_at: todayIso(),
    description: '',
  })

  const handleSubmit = async () => {
    if (closing) {
      if (!requireFields(['closed_at'])) return
      onSaved(await closePlot(plot.id, {
        closed_at: values.closed_at,
        description: textOrNull(values.description),
      }))
    } else {
      onSaved(await reopenPlot(plot.id, { description: textOrNull(values.description) }))
    }
  }

  return (
    <FormDialog
      title={closing ? `Cerrar el lote «${plot.name}»` : `Reabrir el lote «${plot.name}»`}
      icon={closing ? Archive : RotateCcw}
      tone={closing ? 'danger' : 'default'}
      submitLabel={closing ? 'Cerrar lote' : 'Reabrir lote'}
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <p className="text-sm text-gray-600">
        {closing
          ? 'El cierre es definitivo: úsalo cuando el lote deje de dar cosecha. Si el terreno se vuelve a sembrar, se registra como un lote nuevo con «Renovar terreno».'
          : 'Reabrir solo corrige un cierre hecho por error. Si el terreno se volvió a sembrar, usa «Renovar terreno».'}
      </p>
      <FormSection>
        {closing && <DateField label="Fecha de cierre" required max={todayIso()} {...bind('closed_at')} />}
        <TextAreaField
          label={closing ? 'Motivo' : 'Por qué se corrige el cierre'}
          placeholder={closing ? 'Ej. el cultivo dejó de producir' : undefined}
          {...bind('description')}
        />
      </FormSection>
    </FormDialog>
  )
}
