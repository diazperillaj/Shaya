import type {
  Conversation,
  ConversationDetail,
  StreamCallbacks,
} from '../models/types'

/**
 * Base del microservicio del chatbot. En producción nginx enruta
 * /chat/ → chatbot:8005; en dev el proxy de Vite hace lo mismo.
 * La cookie de sesión viaja con credentials: 'include'.
 */
const BASE = '/chat/api/v1'

// ─── CRUD de conversaciones ──────────────────────────────────────────────────

export const fetchConversations = async (): Promise<Conversation[]> => {
  const res = await fetch(`${BASE}/conversations`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo conversaciones')
  return res.json()
}

export const createConversation = async (): Promise<Conversation> => {
  const res = await fetch(`${BASE}/conversations`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!res.ok) throw new Error('Error creando la conversación')
  return res.json()
}

export const fetchConversation = async (id: number): Promise<ConversationDetail> => {
  const res = await fetch(`${BASE}/conversations/${id}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo la conversación')
  return res.json()
}

export const deleteConversation = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE}/conversations/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error eliminando la conversación')
}

// ─── Turno del asistente (SSE sobre fetch) ───────────────────────────────────

/**
 * Envía un mensaje y consume la respuesta SSE del microservicio.
 *
 * Se usa fetch + ReadableStream (no EventSource) porque el endpoint es POST
 * y necesita la cookie de sesión. Eventos: status | text_delta | done | error.
 */
export const streamMessage = async (
  conversationId: number,
  text: string,
  callbacks: StreamCallbacks,
  signal: AbortSignal,
): Promise<void> => {
  const res = await fetch(`${BASE}/conversations/${conversationId}/messages`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
    signal,
  })

  if (!res.ok || !res.body) {
    let detail = 'Error enviando el mensaje'
    try {
      const data = await res.json()
      detail = data.detail || detail
    } catch {
      /* respuesta sin JSON */
    }
    throw new Error(detail)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  // Protocolo SSE: eventos separados por línea en blanco.
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      dispatchSse(rawEvent, callbacks)
    }
  }
}

const dispatchSse = (rawEvent: string, callbacks: StreamCallbacks): void => {
  let event = 'message'
  let data = ''

  for (const rawLine of rawEvent.split('\n')) {
    const line = rawLine.replace(/\r$/, '')
    if (line.startsWith(':')) continue // heartbeat/comentario
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  if (!data) return

  let payload: any
  try {
    payload = JSON.parse(data)
  } catch {
    return // evento malformado: se ignora, el `done`/`error` cierran el turno
  }

  switch (event) {
    case 'status':
      callbacks.onStatus(payload.tool, payload.label)
      break
    case 'text_delta':
      callbacks.onTextDelta(payload.text)
      break
    case 'done':
      callbacks.onDone(payload)
      break
    case 'error':
      callbacks.onError(payload.detail)
      break
  }
}
