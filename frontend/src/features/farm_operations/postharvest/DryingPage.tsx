import { useCallback, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { GitBranch, PackageCheck, Pencil, Plus, RotateCcw, Sun, Warehouse, X } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { inputClass } from '../components/styles'
import { Badge, Button, Card, DetailList, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtDateTime, fmtNumber, plural, todayIso } from '../format'
import { DRYING_DESTINATION_LABELS, PROCESS_STATUS_LABELS } from '../models/labels'
import type { Drying } from '../models/types'
import QualityCard from '../quality/QualityCard'
import { addHumidityCheck, deleteHumidityCheck, fetchDrying, reopenDrying } from '../services/postharvest.api'
import CompositionBars from './CompositionBars'
import { DryingCloseDialog, ToInventoryDialog } from './DryingCloseDialog'
import DryingFormDialog from './DryingFormDialog'
import { dryingMethodName } from './describe'

/**
 * Un secado: el café lavado que entró, las mediciones de humedad, la
 * composición por lote y el cierre con su destino. Con destino inventario
 * queda enlazado al pergamino del inventario.
 */
export default function DryingPage() {
  const { dryingId } = useParams()
  return <DryingView key={dryingId} id={Number(dryingId)} />
}

type Dialog = 'edit' | 'close' | 'inventory' | 'reopen' | null

function DryingView({ id }: { id: number }) {
  const navigate = useNavigate()
  const load = useCallback(() => fetchDrying(id), [id])
  const { data: drying, error, reload } = useLoader(load)
  const [dialog, setDialog] = useState<Dialog>(null)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link to="/cultivo" className="text-sm text-emerald-800 hover:underline">← Volver a las fincas</Link>
        <ErrorMessage message={error} />
      </div>
    )
  }
  if (!drying) return <Loading />

  const inProgress = drying.status === 'in_progress'
  const refresh = () => {
    setDialog(null)
    reload()
  }
  const [min, max] = drying.humidity_range

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={Sun}
        back={{ to: `/cultivo/fincas/${drying.farm_id}/poscosecha`, label: 'Beneficio y secado' }}
        title={
          <span className="flex flex-wrap items-center gap-2">
            Secado {drying.id}
            <Badge tone={inProgress ? 'green' : 'gray'}>{PROCESS_STATUS_LABELS[drying.status]}</Badge>
          </span>
        }
        subtitle={`${dryingMethodName(drying)} · ${
          inProgress ? `desde el ${fmtDate(drying.start_date)}` : `del ${fmtDate(drying.start_date)} al ${fmtDate(drying.end_date)}`
        } · ${plural(drying.days, 'día', 'días')}`}
        actions={
          <>
            <Button icon={GitBranch} onClick={() => navigate(`/cultivo/secados/${drying.id}/trazabilidad`)}>
              Trazabilidad
            </Button>
            {inProgress && <Button icon={Pencil} onClick={() => setDialog('edit')}>Editar</Button>}
            {inProgress && (
              <Button variant="primary" icon={PackageCheck} onClick={() => setDialog('close')}>Cerrar secado</Button>
            )}
            {drying.destination === 'stored' && (
              <Button variant="primary" icon={Warehouse} onClick={() => setDialog('inventory')}>Enviar al inventario</Button>
            )}
            {!inProgress && drying.parchment_id === null && (
              <Button icon={RotateCcw} onClick={() => setDialog('reopen')}>Reabrir</Button>
            )}
          </>
        }
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {(
          [
            ['Café lavado que entró', fmtNumber(drying.wet_kg, 1, 'kg'), `${fmtNumber(drying.cherry_kg_traced, 1, 'kg')} de cereza`],
            ['Pergamino seco', fmtNumber(drying.output_kg, 1, 'kg'), drying.sack_count ? plural(drying.sack_count, 'bulto', 'bultos') : undefined],
            ['Rendimiento', drying.yield_pct !== null ? `${fmtNumber(drying.yield_pct, 1)} %` : '—', 'Pergamino seco / cereza'],
            ['Humedad final', fmtNumber(drying.final_humidity_pct, 2, '%'), `Esperado ${fmtNumber(min, 1)}–${fmtNumber(max, 1, '%')}`],
          ] as [string, string, string?][]
        ).map(([label, value, detail]) => (
          <div key={label} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="mt-1 text-xl font-semibold text-gray-900">{value}</p>
            {detail && <p className="text-xs text-gray-400">{detail}</p>}
          </div>
        ))}
      </div>

      {!inProgress && <Storage drying={drying} />}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Composición por lote">
          <CompositionBars plots={drying.composition} />
        </Card>
        <Card title="Café que entró">
          <ul className="divide-y divide-gray-100">
            {drying.inputs.map((input) => (
              <li key={input.wet_processing_id} className="flex items-center justify-between gap-3 py-2">
                <Link to={`/cultivo/beneficios/${input.wet_processing_id}`} className="text-sm text-gray-900 hover:text-emerald-800">
                  Beneficio {input.wet_processing_id}
                  {input.pulped_at && <span className="text-gray-500"> · {fmtDateTime(input.pulped_at)}</span>}
                </Link>
                <span className="text-sm font-medium text-gray-900">{fmtNumber(input.wet_kg, 3, 'kg')}</span>
              </li>
            ))}
          </ul>
        </Card>
        <HumidityCard drying={drying} onChanged={reload} />
        <QualityCard stage="parchment" target={{ drying_id: drying.id }} />
      </div>

      {dialog === 'edit' && (
        <DryingFormDialog
          farmId={drying.farm_id}
          drying={drying}
          onClose={() => setDialog(null)}
          onSaved={(savedId) => (savedId === null ? navigate(`/cultivo/fincas/${drying.farm_id}/poscosecha`) : refresh())}
        />
      )}
      {dialog === 'close' && <DryingCloseDialog drying={drying} onClose={() => setDialog(null)} onSaved={refresh} />}
      {dialog === 'inventory' && <ToInventoryDialog drying={drying} onClose={() => setDialog(null)} onSaved={refresh} />}
      {dialog === 'reopen' && (
        <FormDialog
          title={`Reabrir el secado ${drying.id}`}
          description="Solo corrige un cierre hecho por error: vuelve a quedar en curso, sin fecha de fin ni destino."
          icon={RotateCcw}
          submitLabel="Reabrir"
          onClose={() => setDialog(null)}
          onSubmit={async () => {
            await reopenDrying(drying.id)
            refresh()
          }}
        />
      )}
    </div>
  )
}

/** Almacenamiento y destino de un secado cerrado */
function Storage({ drying }: { drying: Drying }) {
  return (
    <Card title="Almacenamiento y destino">
      <DetailList
        items={[
          ['Destino', drying.destination ? DRYING_DESTINATION_LABELS[drying.destination] : '—'],
          ['Empaque', drying.packaging ?? '—'],
          ['Fecha de empaque', fmtDate(drying.packed_at)],
          ['Bodega o lugar', drying.storage_place ?? '—'],
          ...(drying.parchment_id !== null
            ? [['En el inventario', `Pergamino n.º ${drying.parchment_id}`] as [string, string]]
            : []),
        ]}
      />
    </Card>
  )
}

/** Mediciones de humedad durante el secado */
function HumidityCard({ drying, onChanged }: { drying: Drying; onChanged: () => void }) {
  const inProgress = drying.status === 'in_progress'
  const [checkDate, setCheckDate] = useState(todayIso())
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  const add = async (e: FormEvent) => {
    e.preventDefault()
    if (!value.trim()) return
    setError(null)
    try {
      await addHumidityCheck(drying.id, { check_date: checkDate, humidity_pct: Number(value) })
      setValue('')
      onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error registrando la medición')
    }
  }

  const remove = async (checkId: number) => {
    setError(null)
    try {
      await deleteHumidityCheck(checkId)
      onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error eliminando la medición')
    }
  }

  return (
    <Card title="Humedad">
      {drying.humidity_checks.length === 0 && (
        <p className="text-sm text-gray-400">Sin mediciones intermedias.</p>
      )}
      {drying.humidity_checks.length > 0 && (
        <ul className="mb-3 divide-y divide-gray-100">
          {drying.humidity_checks.map((check) => (
            <li key={check.id} className="flex items-center justify-between gap-3 py-2 text-sm">
              <span className="text-gray-500">{fmtDate(check.check_date)}</span>
              <span className="flex items-center gap-2">
                <span className="font-medium text-gray-900">{fmtNumber(check.humidity_pct, 2, '%')}</span>
                {inProgress && (
                  <button
                    type="button"
                    onClick={() => remove(check.id)}
                    aria-label={`Eliminar la medición del ${fmtDate(check.check_date)}`}
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-700"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
      {inProgress && (
        <form onSubmit={add} className="flex flex-wrap items-center gap-2">
          <div className="w-40">
            <input
              type="date"
              aria-label="Fecha de la medición"
              value={checkDate}
              max={todayIso()}
              onChange={(e) => setCheckDate(e.target.value)}
              className={`${inputClass()} py-2`}
            />
          </div>
          <div className="w-28">
            <input
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              placeholder="%"
              aria-label="Humedad medida"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className={`${inputClass()} py-2`}
            />
          </div>
          <button
            type="submit"
            className="flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            <Plus className="h-4 w-4" /> Agregar
          </button>
        </form>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </Card>
  )
}
