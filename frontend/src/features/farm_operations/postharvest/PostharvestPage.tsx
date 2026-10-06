import { useCallback, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ChevronRight, Droplet, Factory, Sun } from 'lucide-react'
import { Badge, Button, Card, ErrorMessage, Loading, PageHeader, Pager } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { usePagination } from '../components/usePagination'
import { fmtDate, fmtDateTime, fmtNumber } from '../format'
import { DRYING_DESTINATION_LABELS, PROCESS_STATUS_LABELS } from '../models/labels'
import { fetchFarm } from '../services/farms.api'
import { fetchDryings, fetchWetProcessings } from '../services/postharvest.api'
import { compositionText, dryingMethodName } from './describe'
import DryingFormDialog from './DryingFormDialog'
import WetInputsDialog from './WetInputsDialog'

/**
 * Beneficio y secado de una finca: el camino del café desde la cereza de
 * las cosechas hasta el pergamino seco.
 */
export default function PostharvestPage() {
  const { farmId } = useParams()
  return <Postharvest key={farmId} farmId={Number(farmId)} />
}

function Postharvest({ farmId }: { farmId: number }) {
  const navigate = useNavigate()
  const loadFarm = useCallback(() => fetchFarm(farmId), [farmId])
  const loadWets = useCallback(() => fetchWetProcessings(farmId), [farmId])
  const loadDryings = useCallback(() => fetchDryings(farmId), [farmId])
  const { data: farm } = useLoader(loadFarm)
  const { data: wets, error: wetsError } = useLoader(loadWets)
  const { data: dryings, error: dryingsError } = useLoader(loadDryings)
  const shownWets = usePagination(wets)
  const shownDryings = usePagination(dryings)
  const [dialog, setDialog] = useState<'wet' | 'drying' | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={Factory}
        back={{ to: `/cultivo/fincas/${farmId}`, label: farm?.name ?? 'Finca' }}
        title="Beneficio y secado"
        subtitle="De la cereza de las cosechas al pergamino seco: mezclas, etapas y rendimientos."
        actions={
          <>
            <Button icon={Droplet} onClick={() => setDialog('wet')}>Nuevo beneficio</Button>
            <Button variant="primary" icon={Sun} onClick={() => setDialog('drying')}>Nuevo secado</Button>
          </>
        }
      />

      <Card title="Beneficios">
        {wetsError && <ErrorMessage message={wetsError} />}
        {!wets && !wetsError && <Loading />}
        {wets && wets.length === 0 && (
          <p className="text-sm text-gray-400">
            Aún no hay beneficios. Crea uno con el café cereza de las cosechas de la finca.
          </p>
        )}
        {wets && wets.length > 0 && (
          <ul className="divide-y divide-gray-100">
            {shownWets.visible.map((wet) => (
              <li key={wet.id}>
                <Link to={`/cultivo/beneficios/${wet.id}`} className="-mx-2 flex items-center justify-between gap-3 rounded-xl px-2 py-2.5 hover:bg-gray-50">
                  <span>
                    <span className="flex items-center gap-2 text-sm font-medium text-gray-900">
                      Beneficio {wet.id}
                      <Badge tone={wet.status === 'in_progress' ? 'green' : 'gray'}>{PROCESS_STATUS_LABELS[wet.status]}</Badge>
                    </span>
                    <span className="block text-xs text-gray-500">
                      {wet.pulped_at ? fmtDateTime(wet.pulped_at) : fmtDate(wet.created_at)} ·{' '}
                      {[...new Set(wet.inputs.map((input) => input.plot_name))].join(', ')} ·{' '}
                      {fmtNumber(wet.cherry_kg, 1, 'kg')} cereza
                      {wet.washed_kg !== null && <> → {fmtNumber(wet.washed_kg, 1, 'kg')} lavado</>}
                    </span>
                  </span>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </Link>
              </li>
            ))}
          </ul>
        )}
        <Pager state={shownWets} />
      </Card>

      <Card title="Secados">
        {dryingsError && <ErrorMessage message={dryingsError} />}
        {!dryings && !dryingsError && <Loading />}
        {dryings && dryings.length === 0 && (
          <p className="text-sm text-gray-400">Aún no hay secados. Se secan los beneficios completados.</p>
        )}
        {dryings && dryings.length > 0 && (
          <ul className="divide-y divide-gray-100">
            {shownDryings.visible.map((drying) => (
              <li key={drying.id}>
                <Link to={`/cultivo/secados/${drying.id}`} className="-mx-2 flex items-center justify-between gap-3 rounded-xl px-2 py-2.5 hover:bg-gray-50">
                  <span>
                    <span className="flex flex-wrap items-center gap-2 text-sm font-medium text-gray-900">
                      Secado {drying.id} · {dryingMethodName(drying)}
                      <Badge tone={drying.status === 'in_progress' ? 'green' : 'gray'}>
                        {drying.destination ? DRYING_DESTINATION_LABELS[drying.destination] : PROCESS_STATUS_LABELS[drying.status]}
                      </Badge>
                    </span>
                    <span className="block text-xs text-gray-500">
                      Desde el {fmtDate(drying.start_date)} · {fmtNumber(drying.wet_kg, 1, 'kg')} lavado
                      {drying.output_kg !== null && <> → {fmtNumber(drying.output_kg, 1, 'kg')} pergamino</>}
                      {drying.yield_pct !== null && <> ({fmtNumber(drying.yield_pct, 1)} %)</>}
                    </span>
                    <span className="block text-xs text-gray-400">{compositionText(drying)}</span>
                  </span>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </Link>
              </li>
            ))}
          </ul>
        )}
        <Pager state={shownDryings} />
      </Card>

      {dialog === 'wet' && (
        <WetInputsDialog farmId={farmId} onClose={() => setDialog(null)} onSaved={(id) => navigate(`/cultivo/beneficios/${id}`)} />
      )}
      {dialog === 'drying' && (
        <DryingFormDialog
          farmId={farmId}
          onClose={() => setDialog(null)}
          onSaved={(id) => id !== null && navigate(`/cultivo/secados/${id}`)}
        />
      )}
    </div>
  )
}
