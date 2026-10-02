import { CalendarRange } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, TextAreaField } from '../components/fields'
import { textOrNull, useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import type { CropCycle } from '../models/types'
import { createCycle, deleteCycle, updateCycle } from '../services/cycles.api'

interface CycleFormDialogProps {
  plot: { id: number; name: string }
  /** Ciclo que se corrige; sin él, se abre uno nuevo */
  cycle?: CropCycle
  onClose: () => void
  onSaved: (cycleId: number | null) => void
}

/**
 * Abrir un ciclo productivo en el lote, o corregir sus fechas y
 * observaciones. Un ciclo sin labores se puede eliminar.
 */
export default function CycleFormDialog({ plot, cycle, onClose, onSaved }: CycleFormDialogProps) {
  const closed = cycle?.status === 'closed'
  const { values, bind, requireFields } = useFormValues({
    start_date: cycle?.start_date ?? todayIso(),
    end_date: cycle?.end_date ?? '',
    observations: cycle?.observations ?? '',
  })

  const handleSubmit = async () => {
    if (!requireFields(closed ? ['start_date', 'end_date'] : ['start_date'])) return
    const observations = textOrNull(values.observations)
    const saved = cycle
      ? await updateCycle(cycle.id, {
          start_date: values.start_date,
          end_date: closed ? values.end_date : null,
          observations,
        })
      : await createCycle({ plot_id: plot.id, start_date: values.start_date, observations })
    onSaved(saved.id)
  }

  return (
    <FormDialog
      title={cycle ? `Ciclo ${cycle.cycle_number}` : 'Abrir ciclo'}
      description={
        cycle
          ? `Lote «${plot.name}». Las fechas deben cubrir todas las labores del ciclo.`
          : `Lote «${plot.name}». El ciclo agrupa las labores, la cosecha y el beneficio de una temporada.`
      }
      icon={CalendarRange}
      submitLabel={cycle ? 'Guardar' : 'Abrir ciclo'}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        cycle
          ? {
              label: 'Eliminar ciclo',
              confirm: '¿Eliminar este ciclo? Solo se puede si no tiene labores registradas.',
              onConfirm: async () => {
                await deleteCycle(cycle.id)
                onSaved(null)
              },
            }
          : undefined
      }
    >
      <FormSection>
        <DateField label="Inicio" required max={todayIso()} {...bind('start_date')} />
        {closed && <DateField label="Fin" required max={todayIso()} {...bind('end_date')} />}
        <TextAreaField
          label="Observaciones"
          rows={2}
          placeholder="Ej. inicio de lluvias, cosecha principal"
          {...bind('observations')}
        />
      </FormSection>
    </FormDialog>
  )
}
