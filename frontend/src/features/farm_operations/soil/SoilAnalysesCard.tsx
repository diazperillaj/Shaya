import { useCallback, useState } from 'react'
import { Plus } from 'lucide-react'
import { Button, Card, ErrorMessage } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtNumber } from '../format'
import type { SoilAnalysis } from '../models/types'
import { fetchSoilAnalyses } from '../services/soil.api'
import SoilAnalysisFormDialog from './SoilAnalysisFormDialog'

/** Resultados clave de un análisis en una línea */
const summarize = (analysis: SoilAnalysis): string =>
  [
    analysis.ph !== null && `pH ${fmtNumber(analysis.ph, 2)}`,
    analysis.organic_matter_pct !== null && `M.O. ${fmtNumber(analysis.organic_matter_pct, 2, '%')}`,
    analysis.nitrogen !== null && `N ${fmtNumber(analysis.nitrogen, 2)}`,
    analysis.phosphorus !== null && `P ${fmtNumber(analysis.phosphorus, 2)}`,
    analysis.potassium !== null && `K ${fmtNumber(analysis.potassium, 2)}`,
    analysis.texture,
  ]
    .filter(Boolean)
    .join(' · ')

/**
 * Análisis de suelo del lote. Son del terreno, no de un ciclo: pueden ser
 * anteriores a la siembra.
 */
export default function SoilAnalysesCard({ plotId, canAdd }: { plotId: number; canAdd: boolean }) {
  const load = useCallback(() => fetchSoilAnalyses(plotId), [plotId])
  const { data: analyses, error, reload } = useLoader(load)
  const [dialog, setDialog] = useState<{ analysis?: SoilAnalysis } | null>(null)

  return (
    <Card
      title="Análisis de suelo"
      actions={canAdd ? <Button icon={Plus} onClick={() => setDialog({})}>Agregar</Button> : undefined}
    >
      {error && <ErrorMessage message={error} />}
      {analyses && analyses.length === 0 && (
        <p className="text-sm text-gray-400">Sin análisis registrados. Agrega los resultados del laboratorio.</p>
      )}
      {analyses && analyses.length > 0 && (
        <ul className="divide-y divide-gray-100">
          {analyses.map((analysis) => (
            <li key={analysis.id}>
              <button
                type="button"
                onClick={() => setDialog({ analysis })}
                className="-mx-2 flex w-[calc(100%+1rem)] items-start justify-between gap-3 rounded-xl px-2 py-2.5 text-left hover:bg-gray-50"
              >
                <span>
                  <span className="block text-sm text-gray-900">{summarize(analysis)}</span>
                  {analysis.laboratory && <span className="block text-xs text-gray-400">{analysis.laboratory}</span>}
                </span>
                <span className="whitespace-nowrap text-xs text-gray-400">{fmtDate(analysis.analysis_date)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {dialog && (
        <SoilAnalysisFormDialog
          plotId={plotId}
          analysis={dialog.analysis}
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
