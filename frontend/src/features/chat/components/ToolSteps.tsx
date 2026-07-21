import { useState } from 'react'
import { Check, ChevronDown, ChevronUp, Loader2, Search } from 'lucide-react'
import type { ToolStep } from '../models/types'

interface Props {
  steps: ToolStep[]
  /** true mientras el turno sigue en streaming (chips expandidos) */
  active: boolean
}

/**
 * Chips de los pasos de consulta del agente ("Consultando ventas… ✓").
 * Durante el streaming se muestran expandidos; al terminar se colapsan
 * en un resumen clicable — transparencia sin ruido.
 */
export default function ToolSteps({ steps, active }: Props) {
  const [expanded, setExpanded] = useState(false)
  if (steps.length === 0) return null

  const open = active || expanded

  return (
    <div className="mb-2">
      {!active && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-emerald-700 transition-colors"
        >
          <Search className="w-3 h-3" />
          {steps.length === 1 ? '1 consulta realizada' : `${steps.length} consultas realizadas`}
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      )}

      {open && (
        <div className="flex flex-wrap gap-1.5 mt-1.5">
          {steps.map((step, i) => (
            <span
              key={i}
              className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border transition-colors ${
                step.done
                  ? 'bg-emerald-50 border-emerald-100 text-emerald-800'
                  : 'bg-white border-gray-200 text-gray-600'
              }`}
            >
              {step.done ? (
                <Check className="w-3 h-3 text-emerald-600" />
              ) : (
                <Loader2 className="w-3 h-3 animate-spin text-emerald-600" />
              )}
              {step.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
