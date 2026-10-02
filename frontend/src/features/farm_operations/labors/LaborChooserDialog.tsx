import { ClipboardList } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import type { LaborKind } from '../models/types'
import { LABOR_INFO, LABOR_KINDS } from './laborConfig'

/**
 * Elegir qué labor registrar: botones grandes, pensados para el celular.
 * Con `onlyBulk`, solo las labores que se registran en varios lotes.
 */
export default function LaborChooserDialog({
  description,
  onlyBulk = false,
  onChoose,
  onClose,
}: {
  description: string
  onlyBulk?: boolean
  onChoose: (kind: LaborKind) => void
  onClose: () => void
}) {
  const kinds = LABOR_KINDS.filter((kind) => !onlyBulk || LABOR_INFO[kind].bulk)

  return (
    <FormDialog
      title="Registrar labor"
      description={description}
      icon={ClipboardList}
      submitLabel={null}
      onClose={onClose}
      onSubmit={async () => onClose()}
    >
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {kinds.map((kind) => {
          const { icon: Icon, label, hint } = LABOR_INFO[kind]
          return (
            <button
              key={kind}
              type="button"
              onClick={() => onChoose(kind)}
              className="flex items-center gap-3 rounded-xl border border-gray-100 px-4 py-3 text-left transition hover:border-emerald-200 hover:bg-emerald-50"
            >
              <span className="rounded-lg bg-emerald-100 p-2">
                <Icon className="h-5 w-5 text-emerald-800" />
              </span>
              <span>
                <span className="block text-sm font-medium text-gray-900">{label}</span>
                <span className="block text-xs text-gray-500">{hint}</span>
              </span>
            </button>
          )
        })}
      </div>
    </FormDialog>
  )
}
