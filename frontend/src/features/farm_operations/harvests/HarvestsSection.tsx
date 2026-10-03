import { useCallback, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Apple, ChevronRight } from 'lucide-react'
import { Badge, Button, ErrorMessage } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtMoney, fmtNumber } from '../format'
import type { CropCycle } from '../models/types'
import { fetchHarvests } from '../services/harvests.api'
import HarvestFormDialog from './HarvestFormDialog'

/**
 * Pasadas de cosecha de un ciclo. Cada una abre su página de trabajo;
 * solo puede haber una abierta a la vez.
 */
export default function HarvestsSection({ cycle, canOpen }: { cycle: CropCycle; canOpen: boolean }) {
  const navigate = useNavigate()
  const load = useCallback(() => fetchHarvests(cycle.id), [cycle.id])
  const { data: harvests, error } = useLoader(load)
  const [opening, setOpening] = useState(false)

  const hasOpen = (harvests ?? []).some((harvest) => harvest.status === 'open')
  const showOpen = canOpen && cycle.status === 'active' && harvests !== null && !hasOpen

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-900">Cosechas</h3>
        {showOpen && <Button icon={Apple} onClick={() => setOpening(true)}>Abrir cosecha</Button>}
      </div>

      {error && <ErrorMessage message={error} />}
      {harvests && harvests.length === 0 && (
        <p className="text-sm text-gray-400">
          {cycle.status === 'active'
            ? 'Sin cosechas en este ciclo. Abre una pasada cuando empiece la recolección.'
            : 'Este ciclo no tuvo cosechas registradas.'}
        </p>
      )}
      {harvests && harvests.length > 0 && (
        <ul className="divide-y divide-gray-100 rounded-xl border border-gray-100">
          {harvests.map((harvest) => (
            <li key={harvest.id}>
              <Link
                to={`/cultivo/cosechas/${harvest.id}`}
                className="flex items-center justify-between gap-3 px-3 py-2.5 hover:bg-gray-50"
              >
                <span>
                  <span className="flex items-center gap-2 text-sm font-medium text-gray-900">
                    Pasada {harvest.pass_number}
                    <Badge tone={harvest.status === 'open' ? 'green' : 'gray'}>
                      {harvest.status === 'open' ? 'Abierta' : 'Cerrada'}
                    </Badge>
                  </span>
                  <span className="block text-xs text-gray-500">
                    {harvest.status === 'open'
                      ? `Desde el ${fmtDate(harvest.start_date)}`
                      : `${fmtDate(harvest.start_date)} – ${fmtDate(harvest.end_date)}`}
                    {' · '}
                    {fmtNumber(harvest.total_cherry_kg ?? harvest.kg_registered, 1, 'kg')}
                    {' · '}
                    {fmtMoney(harvest.value_total)}
                    {harvest.value_pending > 0 && ` · pendiente ${fmtMoney(harvest.value_pending)}`}
                  </span>
                </span>
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </Link>
            </li>
          ))}
        </ul>
      )}

      {opening && (
        <HarvestFormDialog
          cycle={cycle}
          plotName={cycle.plot_name}
          onClose={() => setOpening(false)}
          onSaved={(harvestId) => harvestId !== null && navigate(`/cultivo/cosechas/${harvestId}`)}
        />
      )}
    </section>
  )
}
