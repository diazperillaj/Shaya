import { CloudRain } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, SelectField, TextAreaField } from '../components/fields'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import type { ClimateRecord, Plot } from '../models/types'
import { createClimateRecord, deleteClimateRecord, updateClimateRecord } from '../services/climate.api'

/** Registrar o corregir el clima de un día en la finca o en uno de sus lotes */
export default function ClimateFormDialog({
  farmId,
  plots,
  record,
  onClose,
  onSaved,
}: {
  farmId: number
  /** Lotes activos de la finca, para el clima de un solo lote */
  plots: Plot[]
  record?: ClimateRecord
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, requireFields, setFieldError } = useFormValues({
    record_date: record?.record_date ?? todayIso(),
    plot_id: toInput(record?.plot_id),
    rainfall_mm: toInput(record?.rainfall_mm),
    temp_min_c: toInput(record?.temp_min_c),
    temp_max_c: toInput(record?.temp_max_c),
    observations: record?.observations ?? '',
  })

  // Un registro viejo puede ser de un lote que ya se cerró
  const plotOptions = plots.map((plot) => ({ value: String(plot.id), label: plot.name }))
  if (record?.plot_id && !plots.some((plot) => plot.id === record.plot_id)) {
    plotOptions.push({ value: String(record.plot_id), label: record.plot_name ?? 'Lote cerrado' })
  }

  const handleSubmit = async () => {
    if (!requireFields(['record_date'])) return
    const measured = [values.rainfall_mm, values.temp_min_c, values.temp_max_c, values.observations]
    if (!measured.some((value) => value.trim())) {
      setFieldError('rainfall_mm', 'Registra la lluvia, la temperatura o una observación')
      return
    }
    const [min, max] = [numberOrNull(values.temp_min_c), numberOrNull(values.temp_max_c)]
    if (min !== null && max !== null && min > max) {
      setFieldError('temp_min_c', 'La mínima no puede ser mayor que la máxima')
      return
    }
    const payload = {
      plot_id: values.plot_id ? Number(values.plot_id) : null,
      record_date: values.record_date,
      rainfall_mm: numberOrNull(values.rainfall_mm),
      temp_min_c: min,
      temp_max_c: max,
      observations: textOrNull(values.observations),
    }
    if (record) await updateClimateRecord(record.id, payload)
    else await createClimateRecord(farmId, payload)
    onSaved()
  }

  return (
    <FormDialog
      title={record ? 'Corregir registro de clima' : 'Registrar clima'}
      description="Lluvia y temperaturas del día. Sin lote, aplica a toda la finca."
      icon={CloudRain}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        record
          ? {
              label: 'Eliminar',
              confirm: '¿Eliminar este registro de clima?',
              onConfirm: async () => {
                await deleteClimateRecord(record.id)
                onSaved()
              },
            }
          : undefined
      }
    >
      <FormSection>
        <DateField label="Fecha" required max={todayIso()} {...bind('record_date')} />
        <SelectField label="Dónde" placeholder="Toda la finca" options={plotOptions} {...bind('plot_id')} />
        <NumberField label="Lluvia" unit="mm" step="0.1" min="0" {...bind('rainfall_mm')} />
        <div className="hidden sm:block" />
        <NumberField label="Temperatura mínima" unit="°C" step="0.1" {...bind('temp_min_c')} />
        <NumberField label="Temperatura máxima" unit="°C" step="0.1" {...bind('temp_max_c')} />
        <TextAreaField label="Observaciones" rows={2} placeholder="Granizada, vendaval, helada…" {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
