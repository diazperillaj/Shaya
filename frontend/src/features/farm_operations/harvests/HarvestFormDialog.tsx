import { useState } from 'react'
import { Apple } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, TextAreaField } from '../components/fields'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import WeightField from '../components/WeightField'
import { toKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { todayIso } from '../format'
import type { Harvest } from '../models/types'
import { createHarvest, deleteHarvest, updateHarvest } from '../services/harvests.api'

interface HarvestFormDialogProps {
  /** Ciclo en el que se abre la cosecha */
  cycle: { id: number; cycle_number: number }
  plotName: string
  /** Cosecha que se corrige; sin ella, se abre una pasada nueva */
  harvest?: Harvest
  onClose: () => void
  onSaved: (harvestId: number | null) => void
}

/**
 * Abrir una pasada de cosecha con sus tarifas por defecto, o corregir sus
 * datos. En una cosecha cerrada también se corrigen el fin y el total.
 */
export default function HarvestFormDialog({ cycle, plotName, harvest, onClose, onSaved }: HarvestFormDialogProps) {
  const closed = harvest?.status === 'closed'
  const { values, bind, requireFields } = useFormValues({
    start_date: harvest?.start_date ?? todayIso(),
    rate_per_kg: toInput(harvest?.rate_per_kg),
    rate_per_day: toInput(harvest?.rate_per_day),
    observations: harvest?.observations ?? '',
    end_date: harvest?.end_date ?? '',
    total: toInput(harvest?.total_cherry_kg),
  })
  const [unit, setUnit] = useState<WeightUnit>('kg')

  const handleSubmit = async () => {
    if (!requireFields(closed ? ['start_date', 'end_date', 'total'] : ['start_date'])) return
    const payload = {
      start_date: values.start_date,
      rate_per_kg: numberOrNull(values.rate_per_kg),
      rate_per_day: numberOrNull(values.rate_per_day),
      observations: textOrNull(values.observations),
    }
    const saved = harvest
      ? await updateHarvest(harvest.id, {
          ...payload,
          end_date: closed ? values.end_date : null,
          total_cherry_kg: closed ? toKg(values.total, unit) : null,
        })
      : await createHarvest(cycle.id, payload)
    onSaved(saved.id)
  }

  const totalField = bind('total')

  return (
    <FormDialog
      title={harvest ? `Pasada ${harvest.pass_number}` : 'Abrir cosecha'}
      description={`Lote «${plotName}» · ciclo ${cycle.cycle_number}. Las tarifas son las de por defecto al registrar la recolección.`}
      icon={Apple}
      submitLabel={harvest ? 'Guardar' : 'Abrir cosecha'}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        harvest
          ? {
              label: 'Eliminar',
              confirm: '¿Eliminar esta cosecha? Solo se puede si no tiene recolección registrada.',
              onConfirm: async () => {
                await deleteHarvest(harvest.id)
                onSaved(null)
              },
            }
          : undefined
      }
    >
      <FormSection>
        <DateField label="Inicio" required max={todayIso()} {...bind('start_date')} />
        {closed && <DateField label="Fin" required max={todayIso()} {...bind('end_date')} />}
        <NumberField label="Tarifa por kg" unit="COP" min="0" hint="Pago al peso." {...bind('rate_per_kg')} />
        <NumberField label="Jornal del día" unit="COP" min="0" hint="Pago por día trabajado." {...bind('rate_per_day')} />
        {closed && (
          <WeightField
            label="Total de café cereza"
            required
            value={totalField.value}
            error={totalField.error}
            onChange={totalField.onChange}
            unit={unit}
            onUnitChange={setUnit}
          />
        )}
        <TextAreaField label="Observaciones" rows={2} {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
