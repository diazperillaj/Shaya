import { Link } from 'react-router-dom'
import { fmtNumber } from '../format'

/**
 * Participación de cada lote en el café de un secado, como barras: la
 * mezcla se reparte en proporción a los kg de cereza que aportó cada uno.
 */
export default function CompositionBars({
  plots,
}: {
  plots: { plot_id: number; plot_name: string; variety: string; cherry_kg: number; share_pct: number }[]
}) {
  if (plots.length === 0) return <p className="text-sm text-gray-400">Sin café trazado.</p>

  return (
    <ul className="flex flex-col gap-3">
      {plots.map((plot) => (
        <li key={plot.plot_id}>
          <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2 text-sm">
            <Link to={`/cultivo/lotes/${plot.plot_id}`} className="font-medium text-gray-900 hover:text-emerald-800">
              {plot.plot_name}
              <span className="font-normal text-gray-500"> · {plot.variety}</span>
            </Link>
            <span className="text-gray-700">
              {fmtNumber(plot.share_pct, 1)} % · {fmtNumber(plot.cherry_kg, 1, 'kg')} cereza
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-gray-100" role="presentation">
            <div className="h-full rounded-full bg-emerald-700" style={{ width: `${Math.min(plot.share_pct, 100)}%` }} />
          </div>
        </li>
      ))}
    </ul>
  )
}
