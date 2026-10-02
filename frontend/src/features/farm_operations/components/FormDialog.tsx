import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { Check, Loader2, Trash2, X } from 'lucide-react'

interface FormDialogProps {
  title: string
  icon: LucideIcon
  /** Texto de apoyo bajo el título */
  description?: ReactNode
  submitLabel?: string
  /** `danger` para acciones como cerrar un lote */
  tone?: 'default' | 'danger'
  /** Formularios largos (p. ej. lote) usan un diálogo más ancho */
  wide?: boolean
  onClose: () => void
  /**
   * Guarda el formulario. Si lanza un error, su mensaje se muestra dentro
   * del diálogo; si termina bien, quien abrió el diálogo lo cierra.
   */
  onSubmit: () => Promise<void>
  /** Acción destructiva opcional (p. ej. eliminar), con confirmación */
  destructive?: { label: string; confirm: string; onConfirm: () => Promise<void> }
  children?: ReactNode
}

/**
 * Diálogo de formulario del módulo de cultivo.
 *
 * Muestra los errores de la API dentro del diálogo (sin perder lo escrito),
 * bloquea los botones mientras guarda y se cierra con Escape.
 */
export default function FormDialog({
  title,
  icon: Icon,
  description,
  submitLabel = 'Guardar',
  tone = 'default',
  wide = false,
  onClose,
  onSubmit,
  destructive,
  children,
}: FormDialogProps) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busy) onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [busy, onClose])

  const run = async (action: () => Promise<void>) => {
    setError(null)
    setBusy(true)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error inesperado')
    } finally {
      setBusy(false)
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    run(onSubmit)
  }

  const handleDestructive = () => {
    if (destructive && window.confirm(destructive.confirm)) run(destructive.onConfirm)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4">
      <form
        onSubmit={handleSubmit}
        className={`flex max-h-[92vh] w-full flex-col rounded-t-2xl bg-white text-left shadow-2xl sm:rounded-2xl ${
          wide ? 'sm:max-w-2xl' : 'sm:max-w-lg'
        }`}
      >
        <div className="flex items-start justify-between gap-3 rounded-t-2xl bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 px-5 py-4">
          <div className="flex items-start gap-3">
            <Icon className="mt-0.5 h-5 w-5 flex-shrink-0 text-emerald-100" />
            <div>
              <h2 className="text-base font-semibold text-white">{title}</h2>
              {description && <p className="mt-0.5 text-xs text-emerald-100">{description}</p>}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            aria-label="Cerrar"
            className="rounded-lg p-1.5 text-white/80 transition hover:bg-white/10 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-col gap-6 overflow-y-auto px-5 py-5">{children}</div>

        {error && (
          <p className="mx-5 mb-3 whitespace-pre-line rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center justify-end gap-2 rounded-b-2xl border-t border-gray-100 bg-gray-50 px-5 py-3">
          {destructive && (
            <button
              type="button"
              onClick={handleDestructive}
              disabled={busy}
              className="mr-auto flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" /> {destructive.label}
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={busy}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium text-white shadow-md transition disabled:opacity-60 ${
              tone === 'danger' ? 'bg-red-800 hover:bg-red-900' : 'bg-emerald-900 hover:bg-emerald-950'
            }`}
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            {submitLabel}
          </button>
        </div>
      </form>
    </div>
  )
}
