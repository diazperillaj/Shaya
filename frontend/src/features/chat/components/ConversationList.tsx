import { Loader2, MessageSquare, Plus, Trash2 } from 'lucide-react'
import type { Conversation } from '../models/types'

interface Props {
  conversations: Conversation[]
  loading: boolean
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onDelete: (id: number) => void
}

/** Fecha relativa corta (hoy → hora; este año → día/mes; si no → fecha). */
const relativeDate = (iso: string): string => {
  const date = new Date(iso)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })
  }
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })
  }
  return date.toLocaleDateString('es-CO')
}

/** Lista de conversaciones: nueva, seleccionar y borrar (con confirmación). */
export default function ConversationList({
  conversations,
  loading,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: Props) {
  const handleDelete = (e: React.MouseEvent, conv: Conversation): void => {
    e.stopPropagation()
    const name = conv.title || 'esta conversación'
    if (window.confirm(`¿Eliminar "${name}"? Esta acción no se puede deshacer.`)) {
      onDelete(conv.id)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3">
        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 bg-emerald-900 hover:bg-emerald-800 text-white text-sm font-medium rounded-xl px-4 py-2.5 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" /> Nueva conversación
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1">
        {loading ? (
          <div className="flex justify-center py-8 text-gray-300">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
        ) : conversations.length === 0 ? (
          <p className="text-xs text-gray-400 text-center px-4 py-8">
            Aún no tienes conversaciones. Haz tu primera pregunta.
          </p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`group flex items-start gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                conv.id === activeId
                  ? 'bg-emerald-50 border border-emerald-100'
                  : 'hover:bg-gray-50 border border-transparent'
              }`}
            >
              <MessageSquare
                className={`w-4 h-4 shrink-0 mt-0.5 ${
                  conv.id === activeId ? 'text-emerald-700' : 'text-gray-300'
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {conv.title || 'Nueva conversación'}
                  </p>
                  <span className="text-[10px] text-gray-400 shrink-0">
                    {relativeDate(conv.updated_at)}
                  </span>
                </div>
                {conv.preview && (
                  <p className="text-xs text-gray-400 truncate mt-0.5">
                    {/* el preview viene con markdown crudo: se limpia para la lista */}
                    {conv.preview.replace(/[*`#|_]/g, '').replace(/\s+/g, ' ').trim()}
                  </p>
                )}
              </div>
              <button
                onClick={(e) => handleDelete(e, conv)}
                aria-label="Eliminar conversación"
                className="opacity-0 group-hover:opacity-100 shrink-0 p-1 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
