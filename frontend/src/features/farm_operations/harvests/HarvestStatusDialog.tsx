import { useState } from 'react'
import { CircleCheck, RotateCcw } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection } from '../components/fields'
import { toInput, useFormValues } from '../components/useFormValues'
import WeightField from '../components/WeightField'
import { toKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { fmtNumber, todayIso } from '../format'
import type { Harvest } from '../models/types'
import { closeHarvest, reopenHarvest } from '../services/harvests.api'

/**
 * Cerrar la pasada con su total de café cereza (precargado con lo
 * registrado), o reabrir la última pasada si se cerró por error.
 */
export default function HarvestStatusDialog({
  harvest,
  onClose,
  onSaved,
}: {
  harvest: Harvest
  onClose: () => void
  onSaved: () => void
}) {
  const closing = harvest.status === 'open'
  const { values, bind, requireFields } = useFormValues({
    end_date: todayIso(),
    // Lo registrado en la recolección, o lo ya beneficiado si es más
    total: toInput(Math.max(harvest.kg_registered, harvest.kg_processed) || null),
  })
  const [unit, setUnit] = useState<WeightUnit>('kg')
  const totalField = bind('total')
  const total = toKg(values.total, unit)

  const handleSubmit = async () => {
    if (closing) {
      if (!requireFields(['end_date', 'total'])) return
      await closeHarvest(harvest.id, { end_date: values.end_date, total_cherry_kg: total })
    } else {
      await reopenHarvest(harvest.id)
    }
    onSaved()
  }

  if (!closing) {
    return (
      <FormDialog
        title={`Reabrir la pasada ${harvest.pass_number}`}
        description="Reabrir solo corrige un cierre hecho por error: la cosecha vuelve a recibir recolección y pierde su fin y su total."
        icon={RotateCcw}
        submitLabel="Reabrir cosecha"
        onClose={onClose}
        onSubmit={handleSubmit}
      />
    )
  }

  return (
    <FormDialog
      title={`Cerrar la pasada ${harvest.pass_number}`}
      description="El total de café cereza alimenta el beneficio y los rendimientos."
      icon={CircleCheck}
      submitLabel="Cerrar cosecha"
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection>
        <DateField label="Fecha de fin" required max={todayIso()} {...bind('end_date')} />
        <WeightField
          label="Total de café cereza"
          required
          hint={`Registrado en la recolección: ${fmtNumber(harvest.kg_registered, 3, 'kg')}; ya beneficiado: ${fmtNumber(harvest.kg_processed, 3, 'kg')}. Súmale lo recogido sin pago (familia) o sin pesar.`}
          value={totalField.value}
          error={totalField.error}
          onChange={totalField.onChange}
          unit={unit}
          onUnitChange={setUnit}
        />
        {total !== null && total < harvest.kg_registered && (
          <p className="text-xs text-amber-700 sm:col-span-2">
            El total es menor que lo registrado en la recolección ({fmtNumber(harvest.kg_registered, 3, 'kg')}).
          </p>
        )}
      </FormSection>
    </FormDialog>
  )
}
