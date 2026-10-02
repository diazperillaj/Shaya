import { CalendarCheck, RotateCcw } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection } from '../components/fields'
import { useFormValues } from '../components/useFormValues'
import { todayIso } from '../format'
import type { CropCycle } from '../models/types'
import { closeCycle, reopenCycle } from '../services/cycles.api'

/**
 * Cerrar el ciclo activo al terminar su cosecha, o reabrir el último ciclo
 * si se cerró por error.
 */
export default function CycleStatusDialog({
  cycle,
  onClose,
  onSaved,
}: {
  cycle: CropCycle
  onClose: () => void
  onSaved: () => void
}) {
  const closing = cycle.status === 'active'
  const { values, bind, requireFields } = useFormValues({ end_date: todayIso() })

  const handleSubmit = async () => {
    if (closing) {
      if (!requireFields(['end_date'])) return
      await closeCycle(cycle.id, values.end_date)
    } else {
      await reopenCycle(cycle.id)
    }
    onSaved()
  }

  return closing ? (
    <FormDialog
      title={`Cerrar el ciclo ${cycle.cycle_number}`}
      description="Ciérralo cuando termine su cosecha. Después se pueden completar labores olvidadas dentro de sus fechas."
      icon={CalendarCheck}
      submitLabel="Cerrar ciclo"
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection>
        <DateField label="Fecha de fin" required max={todayIso()} {...bind('end_date')} />
      </FormSection>
    </FormDialog>
  ) : (
    <FormDialog
      title={`Reabrir el ciclo ${cycle.cycle_number}`}
      description="Reabrir solo corrige un cierre hecho por error: el ciclo vuelve a quedar activo y sin fecha de fin."
      icon={RotateCcw}
      submitLabel="Reabrir ciclo"
      onClose={onClose}
      onSubmit={handleSubmit}
    />
  )
}
