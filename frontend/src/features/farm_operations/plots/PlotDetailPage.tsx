import { useCallback, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Archive, BellRing, History, LandPlot, Pencil, RotateCcw, Sprout } from 'lucide-react'
import AlertConfigDialog from '../alerts/AlertConfigDialog'
import CyclePanel from '../cycles/CyclePanel'
import SoilAnalysesCard from '../soil/SoilAnalysesCard'
import { Badge, Button, Card, DetailList, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtMoney, fmtNumber, treesPerHectare } from '../format'
import { PLOT_EVENT_LABELS } from '../models/labels'
import type { Plot, RenewalDefaults } from '../models/types'
import QualityProjectionCard from '../projection/QualityProjectionCard'
import { fetchPlot, fetchPlotEvents, fetchRenewalDefaults } from '../services/plots.api'
import PlotEventDialog from './PlotEventDialog'
import PlotFormDialog from './PlotFormDialog'
import PlotStatusDialog from './PlotStatusDialog'

type Dialog =
  | { kind: 'edit' | 'event' | 'status' | 'alerts' }
  | { kind: 'renew'; defaults: RenewalDefaults }
  | null

/**
 * Detalle de un lote: su siembra, su terreno, la procedencia de la semilla
 * y su historial. Desde aquí se cierra, se reabre o se renueva el terreno.
 *
 * Se monta de nuevo al cambiar de lote (p. ej. al ir al lote que renueva el
 * terreno), para no arrastrar datos ni diálogos del lote anterior.
 */
export default function PlotDetailPage() {
  const { plotId } = useParams()
  return <PlotDetail key={plotId} id={Number(plotId)} />
}

function PlotDetail({ id }: { id: number }) {
  const navigate = useNavigate()

  const loadPlot = useCallback(() => fetchPlot(id), [id])
  const loadEvents = useCallback(() => fetchPlotEvents(id), [id])
  const { data: plot, error, reload: reloadPlot } = useLoader(loadPlot)
  const { data: events, reload: reloadEvents } = useLoader(loadEvents)

  const [dialog, setDialog] = useState<Dialog>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link to="/cultivo/fincas" className="text-sm text-emerald-800 hover:underline">← Volver a las fincas</Link>
        <ErrorMessage message={error} />
      </div>
    )
  }
  if (!plot) return <Loading />

  const active = plot.status === 'active'
  const reloadAll = () => {
    setDialog(null)
    reloadPlot()
    reloadEvents()
  }

  const startRenewal = async () => {
    setActionError(null)
    try {
      setDialog({ kind: 'renew', defaults: await fetchRenewalDefaults(plot.id) })
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Error preparando la renovación')
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={LandPlot}
        back={{ to: `/cultivo/fincas/${plot.farm_id}`, label: plot.farm_name }}
        title={
          <span className="flex flex-wrap items-center gap-2">
            {plot.name}
            <Badge tone={active ? 'green' : 'gray'}>{active ? 'Activo' : 'Cerrado'}</Badge>
          </span>
        }
        subtitle={`${plot.variety} · ${fmtNumber(plot.effective_age_years, 1, 'años')}`}
        actions={
          active ? (
            <>
              <Button icon={History} onClick={() => setDialog({ kind: 'event' })}>Registrar evento</Button>
              <Button icon={BellRing} onClick={() => setDialog({ kind: 'alerts' })}>Alertas</Button>
              <Button icon={Pencil} onClick={() => setDialog({ kind: 'edit' })}>Editar</Button>
              <Button variant="danger" icon={Archive} onClick={() => setDialog({ kind: 'status' })}>Cerrar lote</Button>
            </>
          ) : (
            <>
              {plot.renewed_by_plot_id === null && (
                <Button variant="primary" icon={Sprout} onClick={startRenewal}>Renovar terreno</Button>
              )}
              {plot.renewed_by_plot_id === null && (
                <Button icon={RotateCcw} onClick={() => setDialog({ kind: 'status' })}>Reabrir</Button>
              )}
              <Button icon={Pencil} onClick={() => setDialog({ kind: 'edit' })}>Editar</Button>
            </>
          )
        }
      />

      {actionError && <ErrorMessage message={actionError} />}
      <RenewalNotice plot={plot} />
      <CyclePanel plot={plot} onPlotChanged={reloadPlot} />
      {plot.active_cycle && <QualityProjectionCard key={plot.active_cycle.id} plotId={plot.id} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Siembra">
          <DetailList
            items={[
              ['Variedad', plot.variety],
              plot.planting_date
                ? ['Fecha de siembra', fmtDate(plot.planting_date)]
                : ['Edad al registrarlo', fmtNumber(plot.initial_age_years, 1, 'años')],
              ['Edad efectiva', fmtNumber(plot.effective_age_years, 1, 'años')],
              ['Última zoca', fmtDate(plot.last_zoca_date)],
              ['Plántulas', fmtNumber(plot.seedling_count, 0)],
              ['Distancias', distances(plot)],
              ['Sombrío', plot.shade_type ?? '—'],
            ]}
          />
        </Card>
        <Card title="Terreno">
          <DetailList
            items={[
              ['Área', fmtNumber(plot.area, 2, 'ha')],
              ['Pendiente', fmtNumber(plot.slope, 1, '%')],
              ['Tipo de suelo', plot.soil_type ?? '—'],
              ['Ubicación en la finca', plot.location ?? '—'],
            ]}
          />
        </Card>
        <Card title="Procedencia de la semilla">
          <DetailList
            items={[
              ['Proveedor o almacén', plot.seed_supplier ?? '—'],
              ['Lugar de compra', plot.seed_origin_place ?? '—'],
              ['Fecha de compra', fmtDate(plot.seed_purchase_date)],
              ['Costo', fmtMoney(plot.seed_cost)],
            ]}
          />
        </Card>
        <Card title="Historial del lote">
          {events && events.length === 0 && (
            <p className="text-sm text-gray-400">
              Sin eventos. Registra aquí zocas, resiembras o cambios de sombrío.
            </p>
          )}
          {events && events.length > 0 && (
            <ol className="flex flex-col gap-3 border-l-2 border-emerald-100 pl-4">
              {events.map((event) => (
                <li key={event.id}>
                  <p className="text-xs text-gray-400">{fmtDate(event.event_date)}</p>
                  <p className="text-sm font-medium text-gray-900">
                    {PLOT_EVENT_LABELS[event.event_type]}
                    {event.other_detail && `: ${event.other_detail}`}
                  </p>
                  {event.description && <p className="text-sm text-gray-500">{event.description}</p>}
                </li>
              ))}
            </ol>
          )}
        </Card>
        <SoilAnalysesCard plotId={plot.id} canAdd={active} />
      </div>

      {plot.observations && (
        <Card title="Observaciones">
          <p className="whitespace-pre-line text-sm text-gray-700">{plot.observations}</p>
        </Card>
      )}

      {dialog?.kind === 'edit' && (
        <PlotFormDialog
          farmId={plot.farm_id}
          plot={plot}
          onClose={() => setDialog(null)}
          onSaved={reloadAll}
          onDeleted={() => navigate(`/cultivo/fincas/${plot.farm_id}`)}
        />
      )}
      {dialog?.kind === 'renew' && (
        <PlotFormDialog
          farmId={plot.farm_id}
          renewal={dialog.defaults}
          onClose={() => setDialog(null)}
          onSaved={(renewed) => navigate(`/cultivo/lotes/${renewed.id}`)}
        />
      )}
      {dialog?.kind === 'event' && (
        <PlotEventDialog plotId={plot.id} onClose={() => setDialog(null)} onSaved={reloadAll} />
      )}
      {dialog?.kind === 'status' && (
        <PlotStatusDialog plot={plot} onClose={() => setDialog(null)} onSaved={reloadAll} />
      )}
      {dialog?.kind === 'alerts' && (
        <AlertConfigDialog level={{ kind: 'plot', id: plot.id }} name={plot.name} onClose={() => setDialog(null)} />
      )}
    </div>
  )
}

/** Distancias de siembra y la densidad que resulta */
function distances(plot: Plot): string {
  if (plot.row_spacing_m === null || plot.plant_spacing_m === null) return '—'
  const density = treesPerHectare(plot.row_spacing_m, plot.plant_spacing_m)
  return `${fmtNumber(plot.row_spacing_m, 2)} × ${fmtNumber(plot.plant_spacing_m, 2)} m · ${fmtNumber(density, 0)} árboles/ha`
}

/** Aviso del ciclo de vida: cierre y relación con la renovación del terreno */
function RenewalNotice({ plot }: { plot: Plot }) {
  if (plot.status === 'active' && plot.renewed_from_plot_id === null) return null

  return (
    <div className="flex flex-col gap-1 rounded-2xl border border-emerald-100 bg-emerald-50 px-5 py-3 text-sm text-emerald-900">
      {plot.status === 'closed' && <p>Lote cerrado el {fmtDate(plot.closed_at)}. Su edad quedó congelada en esa fecha.</p>}
      {plot.renewed_by_plot_id !== null && (
        <p>
          El terreno se volvió a sembrar:{' '}
          <Link to={`/cultivo/lotes/${plot.renewed_by_plot_id}`} className="font-medium underline">
            ver el lote nuevo
          </Link>
          .
        </p>
      )}
      {plot.status === 'closed' && plot.renewed_by_plot_id === null && (
        <p>Si el terreno se vuelve a sembrar, regístralo con «Renovar terreno».</p>
      )}
      {plot.renewed_from_plot_id !== null && (
        <p>
          Esta siembra renueva el terreno de un lote anterior:{' '}
          <Link to={`/cultivo/lotes/${plot.renewed_from_plot_id}`} className="font-medium underline">
            ver su historia
          </Link>
          .
        </p>
      )}
    </div>
  )
}
