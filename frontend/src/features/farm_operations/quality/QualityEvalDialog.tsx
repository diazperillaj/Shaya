import { Award } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, TextAreaField } from '../components/fields'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import type { QualityEval, QualityEvalPayload, QualityStage } from '../models/types'
import { createQualityEval, deleteQualityEval, updateQualityEval } from '../services/postharvest.api'
import { QUALITY_FIELDS, QUALITY_RESULTS } from './qualityFields'

/** Registrar o corregir una evaluación de calidad en cereza o en pergamino */
export default function QualityEvalDialog({
  stage,
  target,
  record,
  onClose,
  onSaved,
}: {
  stage: QualityStage
  target: { harvest_id: number } | { drying_id: number }
  record?: QualityEval
  onClose: () => void
  onSaved: () => void
}) {
  const fields = QUALITY_FIELDS[stage]
  const { values, bind, requireFields, setFieldError } = useFormValues({
    eval_date: record?.eval_date ?? todayIso(),
    ripe_pct: toInput(record?.ripe_pct),
    green_pct: toInput(record?.green_pct),
    overripe_pct: toInput(record?.overripe_pct),
    bored_pct: toInput(record?.bored_pct),
    humidity_pct: toInput(record?.humidity_pct),
    defects_pct: toInput(record?.defects_pct),
    yield_factor: toInput(record?.yield_factor),
    score: toInput(record?.score),
    observations: record?.observations ?? '',
  })

  const handleSubmit = async () => {
    if (!requireFields(['eval_date'])) return
    if (!fields.some(({ key }) => values[key].trim())) {
      setFieldError(fields[0].key, 'Registra al menos un resultado')
      return
    }
    // Solo se envían los resultados de la etapa
    const own = new Set<string>(fields.map(({ key }) => key))
    const payload = {
      eval_date: values.eval_date,
      ...Object.fromEntries(QUALITY_RESULTS.map((key) => [key, own.has(key) ? numberOrNull(values[key]) : null])),
      observations: textOrNull(values.observations),
    } as QualityEvalPayload
    if (record) await updateQualityEval(record.id, payload)
    else await createQualityEval(stage, target, payload)
    onSaved()
  }

  return (
    <FormDialog
      title={stage === 'cherry' ? 'Calidad en cereza' : 'Calidad del pergamino'}
      description={
        stage === 'cherry'
          ? 'Composición de una muestra de la cosecha.'
          : 'Humedad, defectos, factor de rendimiento y puntaje del pergamino seco.'
      }
      icon={Award}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        record
          ? {
              label: 'Eliminar',
              confirm: '¿Eliminar esta evaluación?',
              onConfirm: async () => {
                await deleteQualityEval(record.id)
                onSaved()
              },
            }
          : undefined
      }
    >
      <FormSection>
        <DateField label="Fecha" required max={todayIso()} {...bind('eval_date')} />
        <div className="hidden sm:block" />
        {fields.map(({ key, label, unit }) => (
          <NumberField
            key={key}
            label={label}
            unit={unit || undefined}
            step="0.01"
            min="0"
            {...bind(key)}
          />
        ))}
        <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
