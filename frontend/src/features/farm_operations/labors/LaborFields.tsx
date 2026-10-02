import { NumberField, SelectField, TextField } from '../components/fields'
import {
  CULTURAL_PRACTICE_LABELS,
  FERTILIZATION_METHOD_LABELS,
  INTENSITY_LABELS,
  IRRIGATION_METHOD_SUGGESTIONS,
  OTHER_PEST_SUGGESTIONS,
  SEVERITY_LABELS,
  TARGET_SUGGESTIONS,
} from '../models/labels'
import type { LaborKind } from '../models/types'
import type { LaborField } from './laborConfig'

type Bind = (field: LaborField) => { value: string; error?: string; onChange: (value: string) => void }

const options = (labels: Record<string, string>) =>
  Object.entries(labels).map(([value, label]) => ({ value, label }))

/**
 * Campos propios de cada labor, sin la fecha, el insumo ni los montos que
 * se reparten entre lotes (los pone el formulario común).
 */
export default function LaborFields({ kind, bind, practiceType }: { kind: LaborKind; bind: Bind; practiceType: string }) {
  switch (kind) {
    case 'fertilizations':
      return (
        <>
          <SelectField label="Método" required options={options(FERTILIZATION_METHOD_LABELS)} {...bind('method')} />
          <NumberField label="Dosis por árbol" unit="g" step="0.01" min="0" {...bind('dose_per_tree_g')} />
        </>
      )
    case 'phytosanitary-apps':
      return (
        <>
          <TextField label="Contra qué" required suggestions={TARGET_SUGGESTIONS} {...bind('target')} />
          <TextField label="Dosis" placeholder="Ej. 20 cc por bomba de 20 L" {...bind('dose_description')} />
        </>
      )
    case 'irrigations':
      return (
        <>
          <TextField label="Método" suggestions={IRRIGATION_METHOD_SUGGESTIONS} {...bind('irrigation_method')} />
          <NumberField label="Duración" unit="min" min="1" {...bind('duration_minutes')} />
        </>
      )
    case 'pest-monitorings':
      return (
        <>
          <NumberField
            label="Broca"
            unit="%"
            step="0.01"
            min="0"
            hint="Frutos perforados por cada 100 revisados."
            {...bind('broca_pct')}
          />
          <NumberField label="Roya" unit="%" step="0.01" min="0" hint="Árboles con síntomas." {...bind('roya_pct')} />
          <TextField label="Otra plaga" suggestions={OTHER_PEST_SUGGESTIONS} {...bind('other_pest')} />
          <NumberField label="Incidencia de la otra plaga" unit="%" step="0.01" min="0" {...bind('other_pest_pct')} />
          <SelectField label="Severidad" placeholder="Sin indicar" options={options(SEVERITY_LABELS)} {...bind('severity')} />
        </>
      )
    case 'cultural-practices':
      return (
        <>
          <SelectField label="Labor" required options={options(CULTURAL_PRACTICE_LABELS)} {...bind('practice_type')} />
          {practiceType === 'other' && <TextField label="¿Cuál labor?" required {...bind('other_detail')} />}
        </>
      )
    case 'flowering-records':
      return (
        <SelectField
          label="Intensidad"
          required
          hint="La floración principal permite estimar la cosecha (unas 32 semanas después)."
          options={options(INTENSITY_LABELS)}
          {...bind('intensity')}
        />
      )
  }
}
