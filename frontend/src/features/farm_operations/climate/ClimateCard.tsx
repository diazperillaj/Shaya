import { useCallback, useState } from 'react'
import { CloudRain } from 'lucide-react'
import { Button, Card, ErrorMessage } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtNumber } from '../format'
import type { ClimateRecord, Plot } from '../models/types'
import { fetchClimateRecords } from '../services/climate.api'
import ClimateFormDialog from './ClimateFormDialog'

const VISIBLE = 8

/** Temperaturas del día: el rango, o la que se haya medido */
const temperatures = ({ temp_min_c: min, temp_max_c: max }: ClimateRecord): string | null => {
  if (min !== null && max !== null) return `${fmtNumber(min, 1)} a ${fmtNumber(max, 1, '°C')}`
  if (min !== null) return `Mín. ${fmtNumber(min, 1, '°C')}`
  if (max !== null) return `Máx. ${fmtNumber(max, 1, '°C')}`
  return null
}

/** Lluvia y temperaturas de un registro en una línea */
const summarize = (record: ClimateRecord): string =>
  [record.rainfall_mm !== null && `Lluvia ${fmtNumber(record.rainfall_mm, 1, 'mm')}`, temperatures(record)]
    .filter(Boolean)
    .join(' · ') || 'Sin mediciones'

/** Clima registrado a mano en la finca, del más reciente al más antiguo */
export default function ClimateCard({ farmId, plots }: { farmId: number; plots: Plot[] }) {
  const load = useCallback(() => fetchClimateRecords(farmId), [farmId])
  const { data: records, error, reload } = useLoader(load)
  const [dialog, setDialog] = useState<{ record?: ClimateRecord } | null>(null)
  const [showAll, setShowAll] = useState(false)

  const visible = showAll ? records ?? [] : (records ?? []).slice(0, VISIBLE)

  return (
    <Card title="Clima" actions={<Button icon={CloudRain} onClick={() => setDialog({})}>Registrar</Button>}>
      {error && <ErrorMessage message={error} />}
      {records && records.length === 0 && (
        <p className="text-sm text-gray-400">
          Registra la lluvia y las temperaturas: el análisis las cruza con las labores y la cosecha de cada ciclo.
        </p>
      )}
      {visible.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {visible.map((record) => (
            <li key={record.id}>
              <button
                type="button"
                onClick={() => setDialog({ record })}
                className="-mx-2 flex w-[calc(100%+1rem)] items-start justify-between gap-3 rounded-xl px-2 py-2.5 text-left hover:bg-gray-50"
              >
                <span>
                  <span className="block text-sm text-gray-900">{summarize(record)}</span>
                  <span className="block text-xs text-gray-400">
                    {record.plot_name ?? 'Toda la finca'}
                    {record.observations && ` · ${record.observations}`}
                  </span>
                </span>
                <span className="whitespace-nowrap text-xs text-gray-400">{fmtDate(record.record_date)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {records && records.length > VISIBLE && (
        <button
          type="button"
          onClick={() => setShowAll((current) => !current)}
          className="mt-2 text-sm font-medium text-gray-500 hover:text-emerald-800"
        >
          {showAll ? 'Ver menos' : `Ver los ${records.length} registros`}
        </button>
      )}

      {dialog && (
        <ClimateFormDialog
          farmId={farmId}
          plots={plots}
          record={dialog.record}
          onClose={() => setDialog(null)}
          onSaved={() => {
            setDialog(null)
            reload()
          }}
        />
      )}
    </Card>
  )
}
