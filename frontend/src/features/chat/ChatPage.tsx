import { useState } from 'react'
import { Bot, History, X } from 'lucide-react'
import { useChat } from './hooks/useChat'
import ConversationList from './components/ConversationList'
import MessageThread from './components/MessageThread'
import Composer from './components/Composer'
import SuggestionCards from './components/SuggestionCards'

interface Props {
  setActiveMenuItem?: (id: number) => void
  /** Módulo desde el que venía el usuario: personaliza las sugerencias. */
  previousMenuItem?: number | null
}

/**
 * Página del Asistente: panel de conversaciones (drawer en móvil, columna en
 * escritorio) + hilo con streaming SSE. El estado vive en useChat.
 */
export default function ChatPage({ previousMenuItem = null }: Props) {
  const chat = useChat()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const emptyThread = chat.messages.length === 0 && !chat.loadingThread

  const handleSelect = (id: number): void => {
    chat.selectConversation(id)
    setDrawerOpen(false)
  }

  const handleNew = (): void => {
    chat.newConversation()
    setDrawerOpen(false)
  }

  return (
    <div className="h-full flex gap-4 min-h-0">
      {/* ── Panel de conversaciones (columna en md+, drawer en móvil) ── */}
      <aside className="hidden md:flex w-72 shrink-0 flex-col bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
        <ConversationList
          conversations={chat.conversations}
          loading={chat.loadingList}
          activeId={chat.activeId}
          onSelect={handleSelect}
          onNew={handleNew}
          onDelete={chat.removeConversation}
        />
      </aside>

      {/* Drawer móvil (mismo patrón del sidebar principal: overlay + backdrop) */}
      {drawerOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/40 z-30 md:hidden"
            onClick={() => setDrawerOpen(false)}
            aria-hidden
          />
          <div className="fixed inset-y-0 left-0 z-40 w-80 max-w-[85vw] bg-white shadow-2xl md:hidden flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <span className="text-sm font-semibold text-gray-700">Conversaciones</span>
              <button
                onClick={() => setDrawerOpen(false)}
                aria-label="Cerrar"
                className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 min-h-0">
              <ConversationList
                conversations={chat.conversations}
                loading={chat.loadingList}
                activeId={chat.activeId}
                onSelect={handleSelect}
                onNew={handleNew}
                onDelete={chat.removeConversation}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Hilo principal ── */}
      <section className="flex-1 min-w-0 flex flex-col bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 px-4 md:px-6 py-3.5 border-b border-gray-100">
          <button
            onClick={() => setDrawerOpen(true)}
            aria-label="Ver conversaciones"
            className="md:hidden p-2 -ml-1 rounded-xl text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <History className="w-5 h-5" />
          </button>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-800 to-emerald-900 flex items-center justify-center shadow-sm">
            <Bot className="w-5 h-5 text-emerald-100" />
          </div>
          <div className="min-w-0">
            <h1 className="text-sm font-semibold text-gray-800 truncate">Asistente Shaya</h1>
            <p className="text-xs text-gray-400">
              {chat.streaming ? 'Analizando datos…' : 'Analítica del negocio en tiempo real'}
            </p>
          </div>
        </div>

        {/* Hilo o estado vacío */}
        {emptyThread ? (
          <SuggestionCards previousMenuItem={previousMenuItem} onPick={chat.send} />
        ) : (
          <MessageThread
            messages={chat.messages}
            loading={chat.loadingThread}
            onRetry={chat.retry}
            canRetry={!chat.streaming}
          />
        )}

        <Composer
          disabled={chat.streaming}
          streaming={chat.streaming}
          onSend={chat.send}
          onStop={chat.stop}
        />
      </section>
    </div>
  )
}
