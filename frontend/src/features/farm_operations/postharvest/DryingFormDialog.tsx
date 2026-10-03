import { useCallback, useState } from 'react'
import { Sun } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, SelectField, TextAreaField, TextField } from '../components/fields'
import { Loading } from '../components/ui'
import { textOrNull, useFormValues } from '../components/useFormValues'
import { useLoader } from '../components/useLoader'

import { fmtDateTime, fmtNumber, todayIso } from '../format'
import { DRYING_METHOD_LABELS } from '../models/labels'
import type { Drying, DryingMethod, WetProcessing } from '../models/types'
import {
  createDrying,
  deleteDrying,
  fetchWetProcessings,
  updateDrying,
} from '../services/postharvest.api'
import SourceRows from './SourceRows'
import type { Source } from './SourceRows'
import { useSourceAmounts } from './useSourceAmounts'

/** Beneficio completado como origen de café lavado: lo que queda por secar */
function wetSource(wet: WetProcessing, ownKg: number): Source {
  return {
    id: wet.id,
    title: `Beneficio ${wet.id}${wet.pulped_at ? ` · ${fmtDateTime(wet.pulped_at)}` : ''}`,
    detail: `${wet.inputs.map((input) => input.plot_name).join(', ')} · lavado ${fmtNumber(wet.washed_kg, 1, 'kg')}`,
    available: (wet.washed_kg ?? 0) - wet.washed_kg_dried + ownKg,
  }
}

/**
 * Crear un secado (método, inicio y el café lavado de cada beneficio) o
 * corregir sus datos mientras está en curso.
 */
export default function DryingFormDialog({
  farmId,
  drying,
  onClose,
  onSaved,
}: {
  farmId: number
  drying?: Drying
  onClose: () => void
  onSaved: (id: number | null) => void
}) {
  const creating = drying === undefined
  const load = useCallback(() => (creating ? fetchWetProcessings(farmId) : Promise.resolve([])), [creating, farmId])
  const { data: wets } = useLoader<WetProcessing[]>(load)
  const { amounts, unit, change, changeUnit, entries } = useSourceAmounts()
  const [problem, setProblem] = useState<string | null>(null)
  const { values, bind, requireFields } = useFormValues({
    method: drying?.method ?? 'marquesina',
    other_detail: drying?.other_detail ?? '',
    start_date: drying?.start_date ?? todayIso(),
    observations: drying?.observations ?? '',
  })
  const isOther = values.method === 'other'

  const sources = (wets ?? [])
    .filter((wet) => wet.status === 'completed')
    .map((wet) => wetSource(wet, 0))
    .filter((source) => source.available !== null && source.available > 0)

  const handleSubmit = async () => {
    if (!requireFields(isOther ? ['start_date', 'other_detail'] : ['start_date'])) return
    const fields = {
      method: values.method as DryingMethod,
      other_detail: isOther ? textOrNull(values.other_detail) : null,
      start_date: values.start_date,
      observations: textOrNull(values.observations),
    }
    if (drying) {
      onSaved((await updateDrying(drying.id, fields)).id)
      return
    }
    const chosen = entries()
    if (!chosen || chosen.length === 0) {
      setProblem(chosen ? 'Elige al menos un beneficio' : 'Indica los kg de cada beneficio elegido')
      return
    }
    const saved = await createDrying(
      farmId,
      fields,
      chosen.map(({ id, kg }) => ({ wet_processing_id: id, wet_kg: kg })),
    )
    onSaved(saved.id)
  }

  return (
    <FormDialog
      wide={creating}
      title={creating ? 'Nuevo secado' : `Secado ${drying.id}`}
      description={creating ? 'Café lavado de beneficios completados de la finca.' : 'Método, inicio y observaciones.'}
      icon={Sun}
      submitLabel={creating ? 'Crear secado' : 'Guardar'}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        drying
          ? {
              label: 'Eliminar',
              confirm: '¿Eliminar este secado en curso?',
              onConfirm: async () => {
                await deleteDrying(drying.id)
                onSaved(null)
              },
            }
          : undefined
      }
    >
      <FormSection>
        <SelectField
          label="Método"
          required
          options={Object.entries(DRYING_METHOD_LABELS).map(([value, label]) => ({ value, label }))}
          {...bind('method')}
        />
        {isOther ? <TextField label="¿Cuál método?" required {...bind('other_detail')} /> : <div className="hidden sm:block" />}
        <DateField label="Inicio" required max={todayIso()} {...bind('start_date')} />
        <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
      </FormSection>

      {creating && (
        <FormSection title="Café lavado que entra">
          <div className="sm:col-span-2">
            {!wets ? (
              <Loading />
            ) : (
              <SourceRows
                sources={sources}
                amounts={amounts}
                onChange={(id, value) => {
                  change(id, value)
                  setProblem(null)
                }}
                unit={unit}
                onUnitChange={changeUnit}
                emptyText="No hay café lavado por secar: completa un beneficio con sus kg de café lavado."
              />
            )}
            {problem && <p className="mt-2 text-sm text-red-600">{problem}</p>}
          </div>
        </FormSection>
      )}
    </FormDialog>
  )
}
