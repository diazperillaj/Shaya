import { useCallback, useState } from 'react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, TextAreaField } from '../components/fields'
import { useFormValues } from '../components/useFormValues'
import { useLoader } from '../components/useLoader'
import { todayIso } from '../format'
import type { AnyLabor, CycleStatus, LaborKind, Plot, SupplyRef } from '../models/types'
import { bulkCreateLabor, createLabor, deleteLabor, updateLabor } from '../services/labors.api'
import { fetchPlots } from '../services/plots.api'
import LaborFields from './LaborFields'
import { EMPTY_VALUES, LABOR_INFO, amountsPayload, sharedPayload, valuesFromRecord } from './laborConfig'
import type { LaborField } from './laborConfig'
import PlotDistribution from './PlotDistribution'
import SupplyPicker from './SupplyPicker'
import { usePlotDistribution } from './usePlotDistribution'

/** Lote y ciclo en los que se registra la labor */
export interface LaborTarget {
  plot: { id: number; name: string }
  cycle: { id: number; cycle_number: number; status: CycleStatus }
}

type Scope = 'plot' | 'several' | 'farm'

const SCOPE_LABELS: Record<Scope, string> = {
  plot: 'Este lote',
  several: 'Varios lotes',
  farm: 'Toda la finca',
}

interface LaborFormDialogProps {
  kind: LaborKind
  farmId: number
  /** Desde un lote. Sin él, la labor se registra en varios lotes de la finca */
  target?: LaborTarget
  /** Registro que se corrige */
  labor?: AnyLabor
  onClose: () => void
  onSaved: () => void
}

/**
 * Registrar o corregir una labor del ciclo.
 *
 * Las labores que se hacen igual en varios lotes (fertilizar, fumigar,
 * regar…) se pueden registrar en varios a la vez: se guarda un registro por
 * lote y la cantidad y el costo totales se reparten por área, editables
 * antes de guardar.
 */
export default function LaborFormDialog({ kind, farmId, target, labor, onClose, onSaved }: LaborFormDialogProps) {
  const info = LABOR_INFO[kind]
  const editing = labor !== undefined
  const canBulk = !editing && info.bulk && (target === undefined || target.cycle.status === 'active')
  const scopes: Scope[] = editing || !canBulk ? ['plot'] : target ? ['plot', 'several', 'farm'] : ['farm', 'several']

  const [scope, setScope] = useState<Scope>(scopes[0])
  const multi = scope !== 'plot'

  const { values, bind, requireFields, setFieldError } = useFormValues<LaborField>(
    labor ? valuesFromRecord(labor) : { ...EMPTY_VALUES, date: todayIso() },
  )
  const [supply, setSupply] = useState<SupplyRef | null>(
    labor && 'supply' in labor.record ? labor.record.supply : null,
  )
  const [supplyError, setSupplyError] = useState<string>()
  const [plotsError, setPlotsError] = useState<string>()

  // Lotes de la finca, solo si la labor se puede registrar en varios
  const loadPlots = useCallback(() => (canBulk ? fetchPlots(farmId) : Promise.resolve([])), [canBulk, farmId])
  const { data: farmPlots } = useLoader<Plot[]>(loadPlots)
  const activePlots = (farmPlots ?? []).filter((plot) => plot.status === 'active')
  const eligible = activePlots.filter((plot) => plot.active_cycle !== null)
  const withoutCycle = activePlots.filter((plot) => plot.active_cycle === null)

  const distribution = usePlotDistribution(info.amounts, target ? [target.plot.id] : [])
  const selected = scope === 'farm' ? eligible : eligible.filter((plot) => distribution.picked.includes(plot.id))
  const { rowValue, rowAmounts } = distribution.forPlots(selected)

  const changeScope = (next: Scope) => {
    setScope(next)
    setPlotsError(undefined)
    distribution.resetSplit()
  }

  /** Validaciones del formulario; marca los errores y devuelve si todo está bien */
  const validate = (): boolean => {
    const required: LaborField[] = ['date']
    if (kind === 'phytosanitary-apps') required.push('target')
    if (kind === 'cultural-practices' && values.practice_type === 'other') required.push('other_detail')
    if (!multi) info.amounts.filter((amount) => amount.required).forEach((amount) => required.push(amount.field))
    let valid = requireFields(required)

    if (info.supplyTypes && !supply) {
      setSupplyError('Elige el insumo')
      valid = false
    }
    if (kind === 'pest-monitorings' && ![values.broca_pct, values.roya_pct, values.other_pest].some((v) => v.trim())) {
      setFieldError('broca_pct', 'Registra al menos un resultado: broca, roya u otra plaga')
      valid = false
    }
    if (multi) {
      const missingAmount = info.amounts.some(
        (amount) => amount.required && selected.some((plot) => !rowValue(plot.id, amount.field).trim()),
      )
      if (selected.length === 0) {
        setPlotsError('Elige al menos un lote')
        valid = false
      } else if (missingAmount) {
        setPlotsError('Indica la cantidad de cada lote')
        valid = false
      }
    }
    return valid
  }

  const handleSubmit = async () => {
    if (!validate()) return
    const shared = sharedPayload(kind, { ...values, supply_id: supply ? String(supply.id) : '' })

    if (labor) {
      await updateLabor(kind, labor.record.id, { ...shared, ...amountsPayload(kind, values) })
    } else if (!multi && target) {
      await createLabor(kind, { ...shared, ...amountsPayload(kind, values), crop_cycle_id: target.cycle.id })
    } else {
      await bulkCreateLabor(kind, {
        ...shared,
        items: selected.map((plot) => ({
          crop_cycle_id: plot.active_cycle!.id,
          ...amountsPayload(kind, rowAmounts(plot.id)),
        })),
      })
    }
    onSaved()
  }

  const where = labor
    ? `Lote «${labor.record.plot_name}» · ciclo ${labor.record.cycle_number}`
    : target && !multi
      ? `Lote «${target.plot.name}» · ciclo ${target.cycle.cycle_number}${target.cycle.status === 'closed' ? ' (cerrado)' : ''}`
      : 'Un registro por cada lote elegido'

  return (
    <FormDialog
      wide={multi}
      title={`${editing ? 'Corregir' : 'Registrar'} ${info.label.toLowerCase()}`}
      description={where}
      icon={info.icon}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        labor
          ? {
              label: 'Eliminar',
              confirm: `¿Eliminar este registro de ${info.label.toLowerCase()}?`,
              onConfirm: async () => {
                await deleteLabor(kind, labor.record.id)
                onSaved()
              },
            }
          : undefined
      }
    >
      {scopes.length > 1 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-gray-700">Aplicar a</p>
          <div
            role="radiogroup"
            className={`grid gap-1 rounded-xl bg-gray-100 p-1 ${scopes.length === 3 ? 'grid-cols-3' : 'grid-cols-2'}`}
          >
            {scopes.map((option) => (
              <button
                key={option}
                type="button"
                role="radio"
                aria-checked={scope === option}
                onClick={() => changeScope(option)}
                className={`rounded-lg px-2 py-2 text-sm font-medium transition ${
                  scope === option ? 'bg-white text-emerald-900 shadow-sm' : 'text-gray-500 hover:text-gray-800'
                }`}
              >
                {SCOPE_LABELS[option]}
              </button>
            ))}
          </div>
        </div>
      )}

      <FormSection>
        <DateField label={info.dateLabel} required max={todayIso()} {...bind('date')} />
        {info.supplyTypes && (
          <SupplyPicker
            label="Insumo"
            selected={supply}
            onSelect={(next) => {
              setSupply(next)
              setSupplyError(undefined)
            }}
            error={supplyError}
            preferredTypes={info.supplyTypes}
          />
        )}
        <LaborFields kind={kind} bind={bind} practiceType={values.practice_type} />
        {!multi &&
          info.amounts.map((amount) => (
            <NumberField
              key={amount.field}
              label={amount.label}
              required={amount.required}
              unit={amount.unit ?? supply?.unit ?? ''}
              step={amount.step}
              min="0"
              hint={amount.field === 'quantity' ? 'Total aplicado al lote, en la unidad del insumo.' : undefined}
              {...bind(amount.field)}
            />
          ))}
      </FormSection>

      {multi && (
        <FormSection title="Lotes">
          <div className="sm:col-span-2">
            <PlotDistribution
              scope={scope === 'farm' ? 'farm' : 'several'}
              eligible={eligible}
              withoutCycle={withoutCycle}
              selected={selected}
              onToggle={(plotId) => {
                distribution.toggle(plotId)
                setPlotsError(undefined)
              }}
              amounts={info.amounts}
              supplyUnit={supply?.unit ?? null}
              totals={distribution.totals}
              onTotalChange={distribution.setTotal}
              rowValue={rowValue}
              onRowChange={(plotId, field, value) => {
                distribution.setRow(plotId, field, value)
                setPlotsError(undefined)
              }}
              error={plotsError}
            />
          </div>
        </FormSection>
      )}

      <FormSection>
        <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
