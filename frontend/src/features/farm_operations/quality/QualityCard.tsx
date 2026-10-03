import { useCallback, useState } from 'react'
import { Award } from 'lucide-react'
import { Button, Card, ErrorMessage } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtNumber } from '../format'
import type { QualityEval, QualityStage } from '../models/types'
import { fetchQualityEvals } from '../services/postharvest.api'
import QualityEvalDialog from './QualityEvalDialog'
import { QUALITY_FIELDS } from './qualityFields'

/** Resultados de una evaluación en una línea: «Maduros 88 % · Verdes 7 %» */
const summarize = (record: QualityEval): string =>
  QUALITY_FIELDS[record.stage]
    .filter(({ key }) => record[key] !== null)
    .map(({ key, label, unit }) => `${label} ${fmtNumber(record[key], 2, unit || undefined)}`)
    .join(' · ')

/**
 * Evaluaciones de calidad: en cereza dentro de la cosecha, en pergamino
 * dentro del secado.
 */
export default function QualityCard({
  stage,
  target,
  canAdd = true,
}: {
  stage: QualityStage
  target: { harvest_id: number } | { drying_id: number }
  canAdd?: boolean
}) {
  const targetId = 'harvest_id' in target ? target.harvest_id : target.drying_id
  const isHarvest = 'harvest_id' in target
  const load = useCallback(
    () => fetchQualityEvals(isHarvest ? { harvest_id: targetId } : { drying_id: targetId }),
    [isHarvest, targetId],
  )
  const { data: evals, error, reload } = useLoader(load)
  const [dialog, setDialog] = useState<{ record?: QualityEval } | null>(null)

  return (
    <Card
      title={stage === 'cherry' ? 'Calidad en cereza' : 'Calidad del pergamino'}
      actions={canAdd ? <Button icon={Award} onClick={() => setDialog({})}>Evaluar</Button> : undefined}
    >
      {error && <ErrorMessage message={error} />}
      {evals && evals.length === 0 && (
        <p className="text-sm text-gray-400">
          {stage === 'cherry'
            ? 'Registra la composición de una muestra: maduros, verdes, sobremaduros y brocados.'
            : 'Registra la humedad, los defectos, el factor de rendimiento y el puntaje.'}
        </p>
      )}
      {evals && evals.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {evals.map((record) => (
            <li key={record.id}>
              <button
                type="button"
                onClick={() => setDialog({ record })}
                className="-mx-2 flex w-[calc(100%+1rem)] items-start justify-between gap-3 rounded-xl px-2 py-2.5 text-left hover:bg-gray-50"
              >
                <span>
                  <span className="block text-sm text-gray-900">{summarize(record)}</span>
                  {record.observations && <span className="block text-xs text-gray-400">{record.observations}</span>}
                </span>
                <span className="whitespace-nowrap text-xs text-gray-400">{fmtDate(record.eval_date)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {dialog && (
        <QualityEvalDialog
          stage={stage}
          target={target}
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
