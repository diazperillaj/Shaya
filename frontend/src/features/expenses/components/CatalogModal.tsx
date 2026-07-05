import { useState } from 'react'
import { X, Plus, Pencil, Trash2, Check, Tags } from 'lucide-react'

interface CatalogItem {
  id: number
  name: string
}

interface CatalogModalProps {
  title: string
  items: CatalogItem[]
  onClose: () => void
  onCreate: (name: string) => Promise<void>
  onUpdate: (id: number, name: string) => Promise<void>
  onDelete?: (id: number) => Promise<void>
  isAdmin?: boolean
}

/**
 * Modal genérico para administrar catálogos simples (nombre único):
 * categorías de gastos y métodos de pago.
 */
export default function CatalogModal({
  title,
  items,
  onClose,
  onCreate,
  onUpdate,
  onDelete,
  isAdmin = false,
}: CatalogModalProps) {
  const [newName, setNewName] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const run = async (fn: () => Promise<void>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
    } catch (e: any) {
      setError(e.message || 'Error inesperado')
    } finally {
      setBusy(false)
    }
  }

  const handleCreate = () => {
    const name = newName.trim()
    if (!name) return setError('Escribe un nombre')
    run(async () => {
      await onCreate(name)
      setNewName('')
    })
  }

  const handleUpdate = () => {
    const name = editingName.trim()
    if (!name || editingId === null) return
    run(async () => {
      await onUpdate(editingId, name)
      setEditingId(null)
      setEditingName('')
    })
  }

  const handleDelete = (item: CatalogItem) => {
    if (!onDelete) return
    if (!window.confirm(`¿Eliminar "${item.name}"?`)) return
    run(() => onDelete(item.id))
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between flex-shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <Tags className="w-5 h-5" />
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all duration-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex flex-col gap-4 overflow-y-auto scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">
              {error}
            </p>
          )}

          {/* Add new */}
          <div className="flex gap-2">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              placeholder="Nuevo nombre…"
              className="flex-1 text-sm border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-700"
            />
            <button
              onClick={handleCreate}
              disabled={busy}
              className="flex items-center gap-1.5 bg-emerald-900 hover:bg-emerald-950 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-medium shadow-md transition-all"
            >
              <Plus className="w-4 h-4" /> Agregar
            </button>
          </div>

          {/* List */}
          <div className="flex flex-col divide-y divide-gray-100 border border-gray-100 rounded-xl overflow-hidden">
            {items.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-6">Sin registros</p>
            )}
            {items.map((item) => (
              <div key={item.id} className="flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-emerald-50/50 transition-colors">
                {editingId === item.id ? (
                  <>
                    <input
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleUpdate()}
                      autoFocus
                      className="flex-1 text-sm border border-emerald-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-700"
                    />
                    <button
                      onClick={handleUpdate}
                      disabled={busy}
                      className="p-1.5 text-emerald-700 hover:bg-emerald-100 rounded-lg transition-colors"
                      title="Guardar"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => { setEditingId(null); setEditingName('') }}
                      className="p-1.5 text-gray-400 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Cancelar"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <>
                    <span className="flex-1 text-sm text-gray-700">{item.name}</span>
                    <button
                      onClick={() => { setEditingId(item.id); setEditingName(item.name) }}
                      className="p-1.5 text-gray-400 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
                      title="Renombrar"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    {isAdmin && onDelete && (
                      <button
                        onClick={() => handleDelete(item)}
                        disabled={busy}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Eliminar"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex justify-end flex-shrink-0">
          <button
            onClick={onClose}
            className="bg-white hover:bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium shadow-sm border border-gray-200 transition-all"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
