import { useEffect, useRef } from 'react'
import { Loader2 } from 'lucide-react'
import type { ChatMessage } from '../models/types'
import MessageBubble from './MessageBubble'

interface Props {
  messages: ChatMessage[]
  loading: boolean
  onRetry: () => void
  canRetry: boolean
}

/**
 * Hilo de mensajes con auto-scroll inteligente: sigue el stream solo si el
 * usuario está cerca del final (si subió a releer, no lo interrumpe).
 */
export default function MessageThread({ messages, loading, onRetry, canRetry }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const stickToBottomRef = useRef(true)

  const handleScroll = (): void => {
    const el = containerRef.current
    if (!el) return
    stickToBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120
  }

  useEffect(() => {
    const el = containerRef.current
    if (el && stickToBottomRef.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 md:px-6 py-4 space-y-4"
    >
      {messages.map((msg, i) => (
        <MessageBubble
          key={msg.key}
          message={msg}
          onRetry={onRetry}
          canRetry={canRetry && i === messages.length - 1}
        />
      ))}
    </div>
  )
}
