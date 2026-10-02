import { Layers } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, TextAreaField, TextField } from '../components/fields'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import { TEXTURE_SUGGESTIONS } from '../models/labels'
import type { SoilAnalysis } from '../models/types'
import { createSoilAnalysis, deleteSoilAnalysis, updateSoilAnalysis } from '../services/soil.api'

const RESULTS = ['ph', 'organic_matter_pct', 'nitrogen', 'phosphorus', 'potassium', 'texture'] as const

/** Registrar o corregir un análisis de suelo del lote */
export default function SoilAnalysisFormDialog({
  plotId,
  analysis,
  onClose,
  onSaved,
}: {
  plotId: number
  analysis?: SoilAnalysis
  onClose: () => void
  onSaved: () => void
}) {
  const { values, bind, requireFields, setFieldError } = useFormValues({
    analysis_date: analysis?.analysis_date ?? todayIso(),
    ph: toInput(analysis?.ph),
    organic_matter_pct: toInput(analysis?.organic_matter_pct),
    nitrogen: toInput(analysis?.nitrogen),
    phosphorus: toInput(analysis?.phosphorus),
    potassium: toInput(analysis?.potassium),
    texture: analysis?.texture ?? '',
    laboratory: analysis?.laboratory ?? '',
    observations: analysis?.observations ?? '',
  })

  const handleSubmit = async () => {
    if (!requireFields(['analysis_date'])) return
    if (!RESULTS.some((field) => values[field].trim())) {
      setFieldError('ph', 'Registra al menos un resultado del análisis')
      return
    }
    const payload = {
      analysis_date: values.analysis_date,
      ph: numberOrNull(values.ph),
      organic_matter_pct: numberOrNull(values.organic_matter_pct),
      nitrogen: numberOrNull(values.nitrogen),
      phosphorus: numberOrNull(values.phosphorus),
      potassium: numberOrNull(values.potassium),
      texture: textOrNull(values.texture),
      laboratory: textOrNull(values.laboratory),
      observations: textOrNull(values.observations),
    }
    if (analysis) await updateSoilAnalysis(analysis.id, payload)
    else await createSoilAnalysis(plotId, payload)
    onSaved()
  }

  return (
    <FormDialog
      title={analysis ? 'Corregir análisis de suelo' : 'Análisis de suelo'}
      description="Copia los resultados del laboratorio. Los nutrientes, en la unidad que use el laboratorio."
      icon={Layers}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        analysis
          ? {
              label: 'Eliminar',
              confirm: '¿Eliminar este análisis de suelo?',
              onConfirm: async () => {
                await deleteSoilAnalysis(analysis.id)
                onSaved()
              },
            }
          : undefined
      }
    >
      <FormSection>
        <DateField label="Fecha del análisis" required max={todayIso()} {...bind('analysis_date')} />
        <TextField label="Laboratorio" {...bind('laboratory')} />
      </FormSection>
      <FormSection title="Resultados">
        <NumberField label="pH" step="0.01" min="0" {...bind('ph')} />
        <NumberField label="Materia orgánica" unit="%" step="0.01" min="0" {...bind('organic_matter_pct')} />
        <NumberField label="Nitrógeno" step="0.01" min="0" {...bind('nitrogen')} />
        <NumberField label="Fósforo" step="0.01" min="0" {...bind('phosphorus')} />
        <NumberField label="Potasio" step="0.01" min="0" {...bind('potassium')} />
        <TextField label="Textura" suggestions={TEXTURE_SUGGESTIONS} {...bind('texture')} />
        <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
