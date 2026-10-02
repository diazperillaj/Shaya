import { useCallback, useState } from 'react'
import { CalendarCheck, CalendarPlus, CalendarRange, ClipboardPlus, Pencil, RotateCcw } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate } from '../format'
import LaborChooserDialog from '../labors/LaborChooserDialog'
import LaborFormDialog from '../labors/LaborFormDialog'
import LaborHistory from '../labors/LaborHistory'
import { LABOR_KINDS, laborDate } from '../labors/laborConfig'
import type { AnyLabor, CropCycle, LaborKind, Plot } from '../models/types'
import { fetchCycles } from '../services/cycles.api'
import { fetchLabors } from '../services/labors.api'
import CycleFormDialog from './CycleFormDialog'
import CycleStatusDialog from './CycleStatusDialog'

/**
 * Ciclos productivos de un lote y las labores de cada uno.
 *
 * Muestra el ciclo activo (o el último) y deja elegir los anteriores. Desde
 * aquí se abre y se cierra el ciclo y se registran sus labores.
 */
export default function CyclePanel({ plot, onPlotChanged }: { plot: Plot; onPlotChanged: () => void }) {
  const loadCycles = useCallback(() => fetchCycles(plot.id), [plot.id])
  const { data: cycles, error, reload } = useLoader(loadCycles)
  const [chosenId, setChosenId] = useState<number | null>(null)
  const [opening, setOpening] = useState(false)

  const plotActive = plot.status === 'active'
  const current = cycles?.find((cycle) => cycle.id === chosenId) ?? cycles?.[0] ?? null
  const canOpen = plotActive && cycles !== null && !cycles.some((cycle) => cycle.status === 'active')

  /** Algo cambió en los ciclos: recarga la lista y el lote (su ciclo activo) */
  const refresh = (cycleId?: number | null) => {
    if (cycleId !== undefined) setChosenId(cycleId)
    reload()
    onPlotChanged()
  }

  return (
    <Card
      title="Ciclo productivo"
      actions={
        canOpen && cycles.length > 0 ? (
          <Button icon={CalendarPlus} onClick={() => setOpening(true)}>Abrir ciclo nuevo</Button>
        ) : undefined
      }
    >
      {error && <ErrorMessage message={error} />}
      {!cycles && !error && <Loading />}

      {cycles && cycles.length === 0 && (
        <EmptyState
          icon={CalendarRange}
          title={plotActive ? 'Sin ciclos productivos' : 'Este lote no tuvo ciclos registrados'}
          description={
            plotActive
              ? 'Abre un ciclo para registrar las labores, la cosecha y el beneficio de la temporada.'
              : undefined
          }
          action={
            plotActive ? (
              <Button variant="primary" icon={CalendarPlus} onClick={() => setOpening(true)}>Abrir ciclo</Button>
            ) : undefined
          }
        />
      )}

      {cycles && cycles.length > 1 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {cycles.map((cycle) => (
            <button
              key={cycle.id}
              type="button"
              onClick={() => setChosenId(cycle.id)}
              aria-pressed={cycle.id === current?.id}
              className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                cycle.id === current?.id ? 'bg-emerald-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Ciclo {cycle.cycle_number}
              {cycle.status === 'active' && ' · activo'}
            </button>
          ))}
        </div>
      )}

      {cycles && current && (
        <CycleView
          key={current.id}
          plot={plot}
          cycle={current}
          isLast={current.id === cycles[0].id}
          onCycleChanged={refresh}
        />
      )}

      {opening && (
        <CycleFormDialog
          plot={plot}
          onClose={() => setOpening(false)}
          onSaved={(cycleId) => {
            setOpening(false)
            refresh(cycleId)
          }}
        />
      )}
    </Card>
  )
}

type Dialog =
  | { kind: 'edit-cycle' | 'status' | 'chooser' }
  | { kind: 'new-labor'; labor: LaborKind }
  | { kind: 'edit-labor'; labor: AnyLabor }
  | null

/** Un ciclo: sus fechas, sus acciones y sus labores */
function CycleView({
  plot,
  cycle,
  isLast,
  onCycleChanged,
}: {
  plot: Plot
  cycle: CropCycle
  isLast: boolean
  onCycleChanged: (cycleId?: number | null) => void
}) {
  const loadLabors = useCallback(async (): Promise<AnyLabor[]> => {
    const groups = await Promise.all(
      LABOR_KINDS.map(async (kind) =>
        (await fetchLabors(kind, { crop_cycle_id: cycle.id })).map((record) => ({ kind, record }) as AnyLabor),
      ),
    )
    return groups.flat().sort((a, b) => laborDate(b).localeCompare(laborDate(a)) || b.record.id - a.record.id)
  }, [cycle.id])
  const { data: labors, error, reload } = useLoader(loadLabors)
  const [dialog, setDialog] = useState<Dialog>(null)

  const active = cycle.status === 'active'
  const target = { plot, cycle }
  const closeAndReload = () => {
    setDialog(null)
    reload()
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="flex items-center gap-2 font-medium text-gray-900">
            Ciclo {cycle.cycle_number}
            <Badge tone={active ? 'green' : 'gray'}>{active ? 'Activo' : 'Cerrado'}</Badge>
          </p>
          <p className="text-sm text-gray-500">
            {active
              ? `Desde el ${fmtDate(cycle.start_date)}`
              : `Del ${fmtDate(cycle.start_date)} al ${fmtDate(cycle.end_date)}`}
          </p>
          {cycle.observations && <p className="mt-1 text-sm text-gray-500">{cycle.observations}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          {plot.status === 'active' && (
            <Button variant="primary" icon={ClipboardPlus} onClick={() => setDialog({ kind: 'chooser' })}>
              Registrar labor
            </Button>
          )}
          {active && (
            <Button icon={CalendarCheck} onClick={() => setDialog({ kind: 'status' })}>Cerrar ciclo</Button>
          )}
          {!active && isLast && plot.status === 'active' && (
            <Button icon={RotateCcw} onClick={() => setDialog({ kind: 'status' })}>Reabrir</Button>
          )}
          <Button icon={Pencil} onClick={() => setDialog({ kind: 'edit-cycle' })}>Editar</Button>
        </div>
      </div>

      {!active && plot.status === 'active' && (
        <p className="text-xs text-gray-400">
          Ciclo cerrado: puedes completar labores olvidadas con fecha dentro del ciclo.
        </p>
      )}

      {error && <ErrorMessage message={error} />}
      {!labors && !error && <Loading />}
      {labors && <LaborHistory labors={labors} onEdit={(labor) => setDialog({ kind: 'edit-labor', labor })} />}

      {dialog?.kind === 'chooser' && (
        <LaborChooserDialog
          description={`Lote «${plot.name}» · ciclo ${cycle.cycle_number}`}
          onChoose={(labor) => setDialog({ kind: 'new-labor', labor })}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog?.kind === 'new-labor' && (
        <LaborFormDialog
          kind={dialog.labor}
          farmId={plot.farm_id}
          target={target}
          onClose={() => setDialog(null)}
          onSaved={closeAndReload}
        />
      )}
      {dialog?.kind === 'edit-labor' && (
        <LaborFormDialog
          kind={dialog.labor.kind}
          farmId={plot.farm_id}
          labor={dialog.labor}
          onClose={() => setDialog(null)}
          onSaved={closeAndReload}
        />
      )}
      {dialog?.kind === 'status' && (
        <CycleStatusDialog
          cycle={cycle}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            onCycleChanged()
          }}
        />
      )}
      {dialog?.kind === 'edit-cycle' && (
        <CycleFormDialog
          plot={plot}
          cycle={cycle}
          onClose={() => setDialog(null)}
          onSaved={(cycleId) => {
            setDialog(null)
            onCycleChanged(cycleId)
          }}
        />
      )}
    </div>
  )
}
