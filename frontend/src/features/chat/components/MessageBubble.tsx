import { AlertCircle, Bot, RotateCcw } from 'lucide-react'
import type { ChatMessage } from '../models/types'
import Markdown from './Markdown'
import ToolSteps from './ToolSteps'

interface Props {
  message: ChatMessage
  onRetry: () => void
  canRetry: boolean
}

/** Burbuja de mensaje: usuario a la derecha (emerald), asistente a la izquierda. */
export default function MessageBubble({ message, onRetry, canRetry }: Props) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] md:max-w-[70%] bg-emerald-900 text-white rounded-2xl rounded-br-md px-4 py-2.5 text-sm whitespace-pre-wrap shadow-sm">
          {message.text}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2.5">
      <div className="w-8 h-8 shrink-0 rounded-xl bg-gradient-to-br from-emerald-800 to-emerald-900 flex items-center justify-center shadow-sm mt-0.5">
        <Bot className="w-[18px] h-[18px] text-emerald-100" />
      </div>

      <div className="max-w-[85%] md:max-w-[75%] flex-1">
        <ToolSteps steps={message.steps} active={!!message.streaming} />

        {(message.text || message.streaming) && (
          <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-md px-4 py-2.5 text-sm text-gray-800 shadow-sm">
            <Markdown text={message.text} />
            {message.streaming && (
              <span className="inline-block w-1.5 h-4 bg-emerald-600 rounded-sm animate-pulse ml-0.5 align-text-bottom" />
            )}
            {message.stopped && (
              <p className="text-xs text-gray-400 italic mt-1.5">Respuesta detenida.</p>
            )}
          </div>
        )}

        {message.error && (
          <div className="mt-1.5 flex items-start gap-2 bg-red-50 border border-red-100 rounded-2xl px-4 py-2.5 text-sm text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p>{message.error}</p>
              {canRetry && (
                <button
                  onClick={onRetry}
                  className="mt-1.5 inline-flex items-center gap-1.5 text-xs font-medium text-red-700 hover:text-red-900 transition-colors"
                >
                  <RotateCcw className="w-3 h-3" /> Reintentar
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
