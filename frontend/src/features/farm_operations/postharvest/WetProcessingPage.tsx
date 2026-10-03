import { useCallback, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { CircleCheck, Droplet, Loader2, Pencil, RotateCcw, Save, Trash2 } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import {
  DateTimeField,
  FormSection,
  NumberField,
  SelectField,
  TextAreaField,
  TextField,
} from '../components/fields'
import { Badge, Button, Card, DetailList, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import { useLoader } from '../components/useLoader'
import WeightField from '../components/WeightField'
import { toKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { fmtDateTime, fmtNumber, fromLocalInput, toLocalInput } from '../format'
import {
  FERMENTATION_CRITERIA_SUGGESTIONS,
  FERMENTATION_METHOD_LABELS,
  FLOATS_METHOD_SUGGESTIONS,
  PROCESS_STATUS_LABELS,
} from '../models/labels'
import type { FermentationMethod, WetProcessing } from '../models/types'
import {
  completeWetProcessing,
  deleteWetProcessing,
  fetchWetProcessing,
  reopenWetProcessing,
  updateWetProcessing,
} from '../services/postharvest.api'
import WetInputsDialog from './WetInputsDialog'

/**
 * Un beneficio: el café cereza que entró (de una o varias cosechas) y sus
 * etapas — flotes, despulpado, fermentación y lavado —, que se registran a
 * medida que ocurren. Al completarse queda fijo su café lavado.
 */
export default function WetProcessingPage() {
  const { wetProcessingId } = useParams()
  return <WetProcessingView key={wetProcessingId} id={Number(wetProcessingId)} />
}

type Dialog = 'inputs' | 'complete' | 'reopen' | null

function WetProcessingView({ id }: { id: number }) {
  const navigate = useNavigate()
  const load = useCallback(() => fetchWetProcessing(id), [id])
  const { data: wet, error, reload } = useLoader(load)
  const [dialog, setDialog] = useState<Dialog>(null)
  const [formKey, setFormKey] = useState(0)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link to="/cultivo" className="text-sm text-emerald-800 hover:underline">← Volver a las fincas</Link>
        <ErrorMessage message={error} />
      </div>
    )
  }
  if (!wet) return <Loading />

  const inProgress = wet.status === 'in_progress'
  const refresh = () => {
    setDialog(null)
    setFormKey((key) => key + 1)
    reload()
  }
  const yieldWashed = wet.washed_kg !== null && wet.cherry_kg > 0 ? (wet.washed_kg / wet.cherry_kg) * 100 : null

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={Droplet}
        back={{ to: `/cultivo/fincas/${wet.farm_id}/poscosecha`, label: 'Beneficio y secado' }}
        title={
          <span className="flex flex-wrap items-center gap-2">
            Beneficio {wet.id}
            <Badge tone={inProgress ? 'green' : 'gray'}>{PROCESS_STATUS_LABELS[wet.status]}</Badge>
          </span>
        }
        subtitle={`${wet.farm_name}${wet.pulped_at ? ` · despulpado el ${fmtDateTime(wet.pulped_at)}` : ''}`}
        actions={
          inProgress ? (
            <Button variant="primary" icon={CircleCheck} onClick={() => setDialog('complete')}>Completar</Button>
          ) : (
            wet.washed_kg_dried === 0 && (
              <Button icon={RotateCcw} onClick={() => setDialog('reopen')}>Reabrir</Button>
            )
          )
        }
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {(
          [
            ['Cereza que entró', fmtNumber(wet.cherry_kg, 1, 'kg')],
            ['Café lavado', fmtNumber(wet.washed_kg, 1, 'kg'), yieldWashed !== null ? `${fmtNumber(yieldWashed, 1)} % de la cereza` : undefined],
            ['Fermentación', fmtNumber(wet.fermentation_hours, 1, 'horas')],
            ['Ya en secado', fmtNumber(wet.washed_kg_dried, 1, 'kg')],
          ] as [string, string, string?][]
        ).map(([label, value, detail]) => (
          <div key={label} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="mt-1 text-xl font-semibold text-gray-900">{value}</p>
            {detail && <p className="text-xs text-gray-400">{detail}</p>}
          </div>
        ))}
      </div>

      <Card
        title="Café que entró"
        actions={inProgress ? <Button icon={Pencil} onClick={() => setDialog('inputs')}>Cambiar</Button> : undefined}
      >
        <ul className="divide-y divide-gray-100">
          {wet.inputs.map((input) => (
            <li key={input.harvest_id} className="flex items-center justify-between gap-3 py-2">
              <Link to={`/cultivo/cosechas/${input.harvest_id}`} className="text-sm text-gray-900 hover:text-emerald-800">
                {input.plot_name} · ciclo {input.cycle_number} · pasada {input.pass_number}
              </Link>
              <span className="text-sm font-medium text-gray-900">{fmtNumber(input.cherry_kg, 3, 'kg')}</span>
            </li>
          ))}
        </ul>
      </Card>

      {inProgress ? (
        <StagesForm key={formKey} wet={wet} onSaved={refresh} />
      ) : (
        <StagesSummary wet={wet} />
      )}

      {inProgress && (
        <button
          type="button"
          onClick={async () => {
            if (!window.confirm('¿Eliminar este beneficio?')) return
            await deleteWetProcessing(wet.id)
            navigate(`/cultivo/fincas/${wet.farm_id}/poscosecha`)
          }}
          className="flex w-fit items-center gap-2 text-sm font-medium text-red-700 hover:underline"
        >
          <Trash2 className="h-4 w-4" /> Eliminar beneficio
        </button>
      )}

      {dialog === 'inputs' && (
        <WetInputsDialog farmId={wet.farm_id} wetProcessing={wet} onClose={() => setDialog(null)} onSaved={refresh} />
      )}
      {dialog === 'complete' && <CompleteDialog wet={wet} onClose={() => setDialog(null)} onSaved={refresh} />}
      {dialog === 'reopen' && (
        <FormDialog
          title={`Reabrir el beneficio ${wet.id}`}
          description="Solo corrige un beneficio completado por error: vuelve a quedar en curso."
          icon={RotateCcw}
          submitLabel="Reabrir"
          onClose={() => setDialog(null)}
          onSubmit={async () => {
            await reopenWetProcessing(wet.id)
            refresh()
          }}
        />
      )}
    </div>
  )
}

/** Valores del formulario de etapas */
function stageValues(wet: WetProcessing) {
  return {
    floats_kg: toInput(wet.floats_kg),
    floats_method: wet.floats_method ?? '',
    pulped_at: toLocalInput(wet.pulped_at),
    fermentation_start: toLocalInput(wet.fermentation_start),
    fermentation_end: toLocalInput(wet.fermentation_end),
    fermentation_method: wet.fermentation_method ?? '',
    fermentation_other_detail: wet.fermentation_other_detail ?? '',
    fermentation_decided_by: wet.fermentation_decided_by ?? '',
    fermentation_criteria: wet.fermentation_criteria ?? '',
    ambient_temp_c: toInput(wet.ambient_temp_c),
    wash_count: toInput(wet.wash_count),
    washed_kg: toInput(wet.washed_kg),
    observations: wet.observations ?? '',
  }
}

/** Etapas del beneficio en curso, para registrarlas a medida que ocurren */
function StagesForm({ wet, onSaved }: { wet: WetProcessing; onSaved: () => void }) {
  const { values, bind, setFieldError } = useFormValues(stageValues(wet))
  const [unit, setUnit] = useState<WeightUnit>('kg')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isOther = values.fermentation_method === 'other'
  const washed = bind('washed_kg')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (values.fermentation_end && !values.fermentation_start) {
      setFieldError('fermentation_start', 'Indica cuándo empezó')
      return
    }
    if (isOther && !values.fermentation_other_detail.trim()) {
      setFieldError('fermentation_other_detail', 'Campo obligatorio')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await updateWetProcessing(wet.id, {
        floats_kg: numberOrNull(values.floats_kg),
        floats_method: textOrNull(values.floats_method),
        pulped_at: fromLocalInput(values.pulped_at),
        fermentation_start: fromLocalInput(values.fermentation_start),
        fermentation_end: fromLocalInput(values.fermentation_end),
        fermentation_method: (values.fermentation_method || null) as FermentationMethod | null,
        fermentation_other_detail: isOther ? textOrNull(values.fermentation_other_detail) : null,
        fermentation_decided_by: textOrNull(values.fermentation_decided_by),
        fermentation_criteria: textOrNull(values.fermentation_criteria),
        ambient_temp_c: numberOrNull(values.ambient_temp_c),
        wash_count: numberOrNull(values.wash_count),
        washed_kg: toKg(values.washed_kg, unit),
        observations: textOrNull(values.observations),
      })
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error guardando el beneficio')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Etapas">
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <FormSection title="1. Selección de flotes">
          <NumberField label="Flotes retirados" unit="kg" step="0.001" min="0" {...bind('floats_kg')} />
          <TextField label="Método" suggestions={FLOATS_METHOD_SUGGESTIONS} {...bind('floats_method')} />
        </FormSection>
        <FormSection title="2. Despulpado">
          <DateTimeField label="Fecha y hora del despulpado" {...bind('pulped_at')} />
        </FormSection>
        <FormSection title="3. Fermentación">
          <DateTimeField label="Inicio" {...bind('fermentation_start')} />
          <DateTimeField label="Fin" hint="El fermaestro indica el punto de lavado." {...bind('fermentation_end')} />
          <SelectField
            label="Método"
            placeholder="Sin indicar"
            options={Object.entries(FERMENTATION_METHOD_LABELS).map(([value, label]) => ({ value, label }))}
            {...bind('fermentation_method')}
          />
          <NumberField label="Temperatura ambiente" unit="°C" step="0.1" {...bind('ambient_temp_c')} />
          {isOther && <TextField label="¿Cuál método?" required wide {...bind('fermentation_other_detail')} />}
          <TextField label="Quién indicó el punto" {...bind('fermentation_decided_by')} />
          <TextField label="Cómo se decidió" suggestions={FERMENTATION_CRITERIA_SUGGESTIONS} {...bind('fermentation_criteria')} />
        </FormSection>
        <FormSection title="4. Lavado">
          <NumberField label="Lavadas" min="1" {...bind('wash_count')} />
          <WeightField
            label="Café lavado"
            hint="Lo que sale a secado. Al completar el beneficio queda fijo."
            value={washed.value}
            error={washed.error}
            onChange={washed.onChange}
            unit={unit}
            onUnitChange={setUnit}
          />
          <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
        </FormSection>
        {error && <ErrorMessage message={error} />}
        <button
          type="submit"
          disabled={busy}
          className="flex items-center gap-2 self-end rounded-xl bg-emerald-900 px-5 py-2.5 text-sm font-medium text-white shadow-md transition hover:bg-emerald-950 disabled:opacity-60"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Guardar etapas
        </button>
      </form>
    </Card>
  )
}

/** Etapas de un beneficio completado, para consulta */
function StagesSummary({ wet }: { wet: WetProcessing }) {
  const method = wet.fermentation_method
    ? wet.fermentation_method === 'other'
      ? wet.fermentation_other_detail ?? 'Otro'
      : FERMENTATION_METHOD_LABELS[wet.fermentation_method]
    : '—'
  return (
    <Card title="Etapas">
      <DetailList
        items={[
          ['Flotes', `${fmtNumber(wet.floats_kg, 3, 'kg')}${wet.floats_method ? ` · ${wet.floats_method}` : ''}`],
          ['Despulpado', fmtDateTime(wet.pulped_at)],
          ['Fermentación', `${fmtDateTime(wet.fermentation_start)} → ${fmtDateTime(wet.fermentation_end)}`],
          ['Método de fermentación', method],
          ['Punto de lavado', [wet.fermentation_decided_by, wet.fermentation_criteria].filter(Boolean).join(' · ') || '—'],
          ['Temperatura ambiente', fmtNumber(wet.ambient_temp_c, 1, '°C')],
          ['Lavadas', fmtNumber(wet.wash_count, 0)],
          ['Café lavado', fmtNumber(wet.washed_kg, 3, 'kg')],
          ...(wet.observations ? [['Observaciones', wet.observations] as [string, string]] : []),
        ]}
      />
    </Card>
  )
}

/** Completar: el café lavado queda fijo para repartirlo en secados */
function CompleteDialog({ wet, onClose, onSaved }: { wet: WetProcessing; onClose: () => void; onSaved: () => void }) {
  const { values, bind, requireFields } = useFormValues({ washed_kg: toInput(wet.washed_kg) })
  const [unit, setUnit] = useState<WeightUnit>('kg')
  const washed = bind('washed_kg')

  return (
    <FormDialog
      title={`Completar el beneficio ${wet.id}`}
      description={`Entró ${fmtNumber(wet.cherry_kg, 1, 'kg')} de cereza. El café lavado no puede superarla.`}
      icon={CircleCheck}
      submitLabel="Completar"
      onClose={onClose}
      onSubmit={async () => {
        if (!requireFields(['washed_kg'])) return
        await completeWetProcessing(wet.id, toKg(values.washed_kg, unit))
        onSaved()
      }}
    >
      <FormSection>
        <WeightField
          label="Café lavado"
          required
          value={washed.value}
          error={washed.error}
          onChange={washed.onChange}
          unit={unit}
          onUnitChange={setUnit}
        />
      </FormSection>
    </FormDialog>
  )
}
