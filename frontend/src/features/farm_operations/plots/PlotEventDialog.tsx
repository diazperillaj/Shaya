import { History } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, SelectField, TextAreaField, TextField } from '../components/fields'
import { textOrNull, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import { MANUAL_EVENT_TYPES, PLOT_EVENT_LABELS } from '../models/labels'
import type { PlotEventType } from '../models/types'
import { createPlotEvent } from '../services/plots.api'

/**
 * Registrar un evento en el historial del lote: zoca, resiembra parcial,
 * cambio de sombrío u otro. El cierre y la reapertura tienen su propia acción.
 */
export default function PlotEventDialog({
  plotId,
  onClose,
  onSaved,
}: {
  plotId: number
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, requireFields } = useFormValues({
    event_type: 'zoca',
    other_detail: '',
    event_date: todayIso(),
    description: '',
  })
  const isOther = values.event_type === 'other'

  const handleSubmit = async () => {
    if (!requireFields(isOther ? ['event_date', 'other_detail'] : ['event_date'])) return
    await createPlotEvent(plotId, {
      event_type: values.event_type as PlotEventType,
      event_date: values.event_date,
      other_detail: isOther ? textOrNull(values.other_detail) : null,
      description: textOrNull(values.description),
    })
    onSaved()
  }

  return (
    <FormDialog
      title="Registrar evento"
      description="Queda en el historial del lote con su fecha."
      icon={History}
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection>
        <SelectField
          label="Evento"
          required
          options={MANUAL_EVENT_TYPES.map((type) => ({ value: type, label: PLOT_EVENT_LABELS[type] }))}
          hint={values.event_type === 'zoca' ? 'La edad del cultivo se vuelve a contar desde la zoca.' : undefined}
          {...bind('event_type')}
        />
        <DateField label="Fecha" required max={todayIso()} {...bind('event_date')} />
        {isOther && <TextField label="¿Cuál evento?" required wide {...bind('other_detail')} />}
        <TextAreaField label="Descripción" {...bind('description')} />
      </FormSection>
    </FormDialog>
  )
}
