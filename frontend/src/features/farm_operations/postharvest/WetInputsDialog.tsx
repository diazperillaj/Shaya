import { useCallback, useState } from 'react'
import { Droplet } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { Loading } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtNumber } from '../format'
import type { Harvest, WetProcessing } from '../models/types'
import { fetchFarmHarvests } from '../services/harvests.api'
import { createWetProcessing, replaceWetInputs } from '../services/postharvest.api'
import SourceRows from './SourceRows'
import type { Source } from './SourceRows'
import { useSourceAmounts } from './useSourceAmounts'

/** Cosecha como origen de café cereza: lo que queda por beneficiar */
function harvestSource(harvest: Harvest, ownKg: number): Source {
  const open = harvest.status === 'open'
  return {
    id: harvest.id,
    title: `${harvest.plot_name} · ciclo ${harvest.cycle_number} · pasada ${harvest.pass_number}`,
    detail: open
      ? `abierta, ${fmtNumber(harvest.kg_registered, 1, 'kg')} registrados`
      : `cerrada, total ${fmtNumber(harvest.total_cherry_kg, 1, 'kg')}`,
    available: open ? null : (harvest.total_cherry_kg ?? 0) - harvest.kg_processed + ownKg,
  }
}

/**
 * Elegir las cosechas de la finca que entran a un beneficio y cuánto café
 * cereza aporta cada una. Sirve para crear el beneficio o para corregir sus
 * aportes mientras está en curso.
 */
export default function WetInputsDialog({
  farmId,
  wetProcessing,
  onClose,
  onSaved,
}: {
  farmId: number
  wetProcessing?: WetProcessing
  onClose: () => void
  onSaved: (id: number) => void
}) {
  const load = useCallback(() => fetchFarmHarvests(farmId), [farmId])
  const { data: harvests } = useLoader(load)
  const own = Object.fromEntries((wetProcessing?.inputs ?? []).map((input) => [input.harvest_id, input.cherry_kg]))
  const { amounts, unit, change, changeUnit, entries } = useSourceAmounts(own)
  const [problem, setProblem] = useState<string | null>(null)

  const sources = (harvests ?? [])
    .map((harvest) => harvestSource(harvest, own[harvest.id] ?? 0))
    .filter((source) => source.available === null || source.available > 0 || source.id in own)

  const handleSubmit = async () => {
    const chosen = entries()
    if (!chosen || chosen.length === 0) {
      setProblem(chosen ? 'Elige al menos una cosecha' : 'Indica los kg de cada cosecha elegida')
      return
    }
    const inputs = chosen.map(({ id, kg }) => ({ harvest_id: id, cherry_kg: kg }))
    const saved = wetProcessing
      ? await replaceWetInputs(wetProcessing.id, inputs)
      : await createWetProcessing(farmId, inputs)
    onSaved(saved.id)
  }

  return (
    <FormDialog
      wide
      title={wetProcessing ? 'Café que entra al beneficio' : 'Nuevo beneficio'}
      description="Elige las cosechas y el café cereza que aporta cada una. Mezclar pasadas o lotes está bien: se reparten por kg en la trazabilidad."
      icon={Droplet}
      submitLabel={wetProcessing ? 'Guardar' : 'Crear beneficio'}
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      {!harvests ? (
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
          emptyText="No hay cosechas con café por beneficiar en esta finca. Abre una pasada en el ciclo de un lote."
        />
      )}
      {problem && <p className="text-sm text-red-600">{problem}</p>}
    </FormDialog>
  )
}
