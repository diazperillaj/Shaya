import { useCallback, useEffect, useRef, useState } from 'react'
import {
  createConversation,
  deleteConversation,
  fetchConversation,
  fetchConversations,
  streamMessage,
} from '../services/chat.api'
import type { ApiMessage, ChatMessage, Conversation } from '../models/types'

let keySeq = 0
const nextKey = (): string => `m${++keySeq}`

/** Extrae el texto plano de los bloques [{type:'text', text}] del historial. */
const blocksToText = (content: unknown): string => {
  if (Array.isArray(content)) {
    return content
      .map((b) => (b && typeof b === 'object' && 'text' in b ? String(b.text) : ''))
      .join('')
  }
  return typeof content === 'string' ? content : ''
}

/**
 * Reconstruye el hilo de la UI desde el historial: los mensajes `tool`
 * quedan como pasos del mensaje assistant que los siguió.
 */
const mapHistory = (messages: ApiMessage[]): ChatMessage[] => {
  const out: ChatMessage[] = []
  let pendingSteps: ChatMessage['steps'] = []

  for (const msg of messages) {
    if (msg.role === 'tool') {
      pendingSteps.push({
        tool: msg.tool_name ?? 'consulta',
        label: msg.tool_name ?? 'consulta',
        done: true,
      })
    } else if (msg.role === 'user') {
      out.push({ key: nextKey(), role: 'user', text: blocksToText(msg.content), steps: [] })
      pendingSteps = []
    } else {
      out.push({
        key: nextKey(),
        role: 'assistant',
        text: blocksToText(msg.content),
        steps: pendingSteps,
      })
      pendingSteps = []
    }
  }
  return out
}

/**
 * Estado y acciones del chat: conversaciones, hilo activo y streaming SSE.
 * Es el único dueño del estado — los componentes son presentacionales.
 */
export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loadingList, setLoadingList] = useState(true)
  const [activeId, setActiveId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingThread, setLoadingThread] = useState(false)
  const [streaming, setStreaming] = useState(false)

  const abortRef = useRef<AbortController | null>(null)
  const lastUserTextRef = useRef<string>('')

  const refreshConversations = useCallback(async (): Promise<void> => {
    try {
      setConversations(await fetchConversations())
    } catch {
      /* la lista no es crítica: el hilo sigue funcionando */
    } finally {
      setLoadingList(false)
    }
  }, [])

  useEffect(() => {
    refreshConversations()
    return () => abortRef.current?.abort()
  }, [refreshConversations])

  /** Actualiza (de forma inmutable) el último mensaje del hilo. */
  const patchLast = useCallback(
    (patch: (last: ChatMessage) => ChatMessage): void => {
      setMessages((prev) =>
        prev.length === 0 ? prev : [...prev.slice(0, -1), patch(prev[prev.length - 1])],
      )
    },
    [],
  )

  const selectConversation = useCallback(async (id: number): Promise<void> => {
    abortRef.current?.abort()
    setActiveId(id)
    setLoadingThread(true)
    setMessages([])
    try {
      const detail = await fetchConversation(id)
      setMessages(mapHistory(detail.messages))
    } catch {
      setMessages([
        {
          key: nextKey(),
          role: 'assistant',
          text: '',
          steps: [],
          error: 'No se pudo cargar la conversación.',
        },
      ])
    } finally {
      setLoadingThread(false)
    }
  }, [])

  const newConversation = useCallback((): void => {
    abortRef.current?.abort()
    setActiveId(null)
    setMessages([])
  }, [])

  const removeConversation = useCallback(
    async (id: number): Promise<void> => {
      await deleteConversation(id)
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (id === activeId) {
        setActiveId(null)
        setMessages([])
      }
    },
    [activeId],
  )

  const send = useCallback(
    async (text: string): Promise<void> => {
      const clean = text.trim()
      if (!clean || streaming) return
      lastUserTextRef.current = clean

      setStreaming(true)
      setMessages((prev) => [
        ...prev,
        { key: nextKey(), role: 'user', text: clean, steps: [] },
        { key: nextKey(), role: 'assistant', text: '', steps: [], streaming: true },
      ])

      const controller = new AbortController()
      abortRef.current = controller

      try {
        // Primera pregunta sin conversación: se crea aquí mismo
        let convId = activeId
        if (convId === null) {
          const conv = await createConversation()
          convId = conv.id
          setActiveId(convId)
        }

        await streamMessage(
          convId,
          clean,
          {
            onStatus: (tool, label) =>
              patchLast((m) => ({
                ...m,
                // el paso anterior termina cuando arranca el siguiente
                steps: [
                  ...m.steps.map((s) => ({ ...s, done: true })),
                  { tool, label, done: false },
                ],
              })),
            onTextDelta: (delta) =>
              patchLast((m) => ({
                ...m,
                text: m.text + delta,
                steps: m.steps.map((s) => ({ ...s, done: true })),
              })),
            onDone: () =>
              patchLast((m) => ({
                ...m,
                streaming: false,
                steps: m.steps.map((s) => ({ ...s, done: true })),
              })),
            onError: (detail) =>
              patchLast((m) => ({ ...m, streaming: false, error: detail })),
          },
          controller.signal,
        )
        // El título lo genera el servicio en el primer turno
        refreshConversations()
      } catch (err: unknown) {
        if (controller.signal.aborted) {
          patchLast((m) => ({
            ...m,
            streaming: false,
            stopped: true,
            steps: m.steps.map((s) => ({ ...s, done: true })),
          }))
        } else {
          const detail = err instanceof Error ? err.message : 'Error de conexión.'
          patchLast((m) => ({ ...m, streaming: false, error: detail }))
        }
      } finally {
        setStreaming(false)
        abortRef.current = null
      }
    },
    [activeId, patchLast, refreshConversations, streaming],
  )

  const stop = useCallback((): void => {
    abortRef.current?.abort()
  }, [])

  /** Reintenta el último mensaje del usuario (quita el turno fallido). */
  const retry = useCallback((): void => {
    const text = lastUserTextRef.current
    if (!text || streaming) return
    setMessages((prev) => prev.slice(0, -2))
    send(text)
  }, [send, streaming])

  return {
    conversations,
    loadingList,
    activeId,
    messages,
    loadingThread,
    streaming,
    selectConversation,
    newConversation,
    removeConversation,
    send,
    stop,
    retry,
  }
}
