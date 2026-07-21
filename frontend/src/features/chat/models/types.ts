/**
 * Tipos de la feature de chat (espejo de los schemas del microservicio).
 */

/** Conversación como la devuelve la API del chatbot. */
export interface Conversation {
  id: number
  title: string | null
  preview?: string | null
  created_at: string
  updated_at: string
}

/** Mensaje crudo del historial (roles user | assistant | tool). */
export interface ApiMessage {
  id: number
  role: 'user' | 'assistant' | 'tool'
  content: unknown
  tool_name?: string | null
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: ApiMessage[]
}

/** Paso de tool mostrado como chip ("🔍 Consultando ventas…"). */
export interface ToolStep {
  tool: string
  label: string
  done: boolean
}

/**
 * Mensaje del hilo en la UI. Los mensajes `tool` del historial se agrupan
 * como `steps` del mensaje assistant que los siguió.
 */
export interface ChatMessage {
  key: string
  role: 'user' | 'assistant'
  text: string
  steps: ToolStep[]
  /** true mientras el stream SSE está activo para este mensaje */
  streaming?: boolean
  /** Mensaje de error del turno (evento SSE `error` o fallo de red) */
  error?: string | null
  /** El usuario detuvo el stream manualmente */
  stopped?: boolean
}

/** Payload del evento SSE `done`. */
export interface StreamDone {
  message_id: number
  usage: { input: number; output: number }
  latency_ms: number
}

/** Callbacks del stream de un turno. */
export interface StreamCallbacks {
  onStatus: (tool: string, label: string) => void
  onTextDelta: (text: string) => void
  onDone: (payload: StreamDone) => void
  onError: (detail: string) => void
}
