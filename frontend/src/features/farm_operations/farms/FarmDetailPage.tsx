import { useCallback, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { BellRing, CirclePlus, ClipboardPlus, LandPlot, MapPinned, Pencil } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import AlertConfigDialog from '../alerts/AlertConfigDialog'
import ClimateCard from '../climate/ClimateCard'
import { Badge, Button, Card, DetailList, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import EmployeesCard from '../employees/EmployeesCard'
import { fmtNumber, plural } from '../format'
import LaborChooserDialog from '../labors/LaborChooserDialog'
import LaborFormDialog from '../labors/LaborFormDialog'
import type { LaborKind, Plot } from '../models/types'
import PlotFormDialog from '../plots/PlotFormDialog'
import { fetchFarm } from '../services/farms.api'
import { fetchPlots } from '../services/plots.api'
import FarmFormDialog from './FarmFormDialog'

type Dialog = 'edit' | 'alerts' | 'new-plot' | 'labor-chooser' | { labor: LaborKind } | null

/**
 * Detalle de una finca: sus datos, sus lotes y sus trabajadores.
 *
 * Se monta de nuevo al cambiar de finca, para no arrastrar sus datos.
 */
export default function FarmDetailPage() {
  const { farmId } = useParams()
  return <FarmDetail key={farmId} id={Number(farmId)} />
}

function FarmDetail({ id }: { id: number }) {
  const navigate = useNavigate()
  const { user } = useAuth()

  const loadFarm = useCallback(() => fetchFarm(id), [id])
  const loadPlots = useCallback(() => fetchPlots(id), [id])
  const { data: farm, error, reload: reloadFarm } = useLoader(loadFarm)
  const { data: plots, reload: reloadPlots } = useLoader(loadPlots)

  const [dialog, setDialog] = useState<Dialog>(null)
  const [showClosed, setShowClosed] = useState(false)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link to="/cultivo" className="text-sm text-emerald-800 hover:underline">← Volver a las fincas</Link>
        <ErrorMessage message={error} />
      </div>
    )
  }
  if (!farm) return <Loading />

  const activePlots = (plots ?? []).filter((plot) => plot.status === 'active')
  const closedPlots = (plots ?? []).filter((plot) => plot.status === 'closed')
  const coordinates =
    farm.latitude !== null && farm.longitude !== null ? `${farm.latitude}, ${farm.longitude}` : '—'

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={MapPinned}
        back={{ to: '/cultivo', label: 'Fincas' }}
        title={
          <span className="flex flex-wrap items-center gap-2">
            {farm.name} {!farm.active && <Badge>Inactiva</Badge>}
          </span>
        }
        subtitle={
          <>
            {farm.village}, {farm.municipality}
            {user?.role === 'admin' && <> · Caficultor: {farm.farmer.full_name}</>}
          </>
        }
        actions={
          <>
            <Button icon={BellRing} onClick={() => setDialog('alerts')}>Alertas</Button>
            <Button icon={Pencil} onClick={() => setDialog('edit')}>Editar</Button>
          </>
        }
      />

      <Card>
        <DetailList
          items={[
            ['Altitud', fmtNumber(farm.altitude, 0, 'm s.n.m.')],
            ['Área total', fmtNumber(farm.total_area, 2, 'ha')],
            ['Coordenadas', coordinates],
            ['Lotes activos', farm.active_plots],
            ...(farm.observations ? [['Observaciones', farm.observations] as [string, string]] : []),
          ]}
        />
      </Card>

      <Card
        title="Lotes"
        actions={
          <>
            {activePlots.length > 0 && (
              <Button icon={ClipboardPlus} onClick={() => setDialog('labor-chooser')}>
                Registrar labor
              </Button>
            )}
            <Button variant="primary" icon={CirclePlus} onClick={() => setDialog('new-plot')}>
              Nuevo lote
            </Button>
          </>
        }
      >
        {plots && activePlots.length === 0 && (
          <p className="text-sm text-gray-400">
            Esta finca no tiene lotes activos. Cada lote es un terreno con su siembra: variedad,
            fecha o edad del cultivo y procedencia de la semilla.
          </p>
        )}
        <PlotList plots={activePlots} />

        {closedPlots.length > 0 && (
          <div className="mt-4 border-t border-gray-100 pt-3">
            <button
              type="button"
              onClick={() => setShowClosed((current) => !current)}
              className="text-sm font-medium text-gray-500 hover:text-emerald-800"
            >
              {showClosed ? 'Ocultar' : 'Ver'} {plural(closedPlots.length, 'lote cerrado', 'lotes cerrados')}
            </button>
            {showClosed && <PlotList plots={closedPlots} />}
          </div>
        )}
      </Card>

      <ClimateCard farmId={farm.id} plots={activePlots} />
      <EmployeesCard farmId={farm.id} />

      {dialog === 'labor-chooser' && (
        <LaborChooserDialog
          description="La misma labor en varios lotes de la finca, con un registro por lote"
          onlyBulk
          onChoose={(labor) => setDialog({ labor })}
          onClose={() => setDialog(null)}
        />
      )}
      {typeof dialog === 'object' && dialog !== null && (
        <LaborFormDialog
          kind={dialog.labor}
          farmId={farm.id}
          onClose={() => setDialog(null)}
          onSaved={() => setDialog(null)}
        />
      )}

      {dialog === 'edit' && (
        <FarmFormDialog
          farm={farm}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            reloadFarm()
          }}
          onDeleted={() => navigate('/cultivo')}
        />
      )}
      {dialog === 'alerts' && (
        <AlertConfigDialog level={{ kind: 'farm', id: farm.id }} name={farm.name} onClose={() => setDialog(null)} />
      )}
      {dialog === 'new-plot' && (
        <PlotFormDialog
          farmId={farm.id}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            reloadPlots()
            reloadFarm()
          }}
        />
      )}
    </div>
  )
}

function PlotList({ plots }: { plots: Plot[] }) {
  if (plots.length === 0) return null
  return (
    <ul className="mt-2 divide-y divide-gray-100">
      {plots.map((plot) => (
        <li key={plot.id}>
          <Link
            to={`/cultivo/lotes/${plot.id}`}
            className="-mx-2 flex flex-wrap items-center justify-between gap-2 rounded-xl px-2 py-3 hover:bg-gray-50"
          >
            <div className="flex items-center gap-3">
              <LandPlot className="h-5 w-5 text-emerald-700" />
              <div>
                <p className="text-sm font-medium text-gray-900">{plot.name}</p>
                <p className="text-xs text-gray-500">
                  {plot.variety} · {fmtNumber(plot.effective_age_years, 1, 'años')}
                  {plot.area !== null && <> · {fmtNumber(plot.area, 2, 'ha')}</>}
                </p>
              </div>
            </div>
            {plot.status === 'closed' ? (
              <Badge>Cerrado</Badge>
            ) : plot.active_cycle ? (
              <Badge tone="green">Ciclo {plot.active_cycle.cycle_number}</Badge>
            ) : (
              <Badge tone="amber">Sin ciclo activo</Badge>
            )}
          </Link>
        </li>
      ))}
    </ul>
  )
}
