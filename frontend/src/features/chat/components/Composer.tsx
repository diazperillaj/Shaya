import { useRef, useState } from 'react'
import { Send, Square } from 'lucide-react'

interface Props {
  disabled: boolean
  streaming: boolean
  onSend: (text: string) => void
  onStop: () => void
}

/**
 * Caja de escritura: Enter envía, Shift+Enter hace salto de línea,
 * y durante el streaming el botón cambia a "detener".
 */
export default function Composer({ disabled, streaming, onSend, onStop }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = (): void => {
    const clean = text.trim()
    if (!clean || disabled) return
    onSend(clean)
    setText('')
    resize('')
  }

  /** Autosize hasta ~5 líneas. */
  const resize = (value: string): void => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`
    if (value === '') el.style.height = 'auto'
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-gray-100 bg-white px-3 md:px-4 py-3">
      <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-3 py-2 focus-within:border-emerald-600 focus-within:ring-1 focus-within:ring-emerald-600/30 transition-colors">
        <textarea
          ref={textareaRef}
          value={text}
          rows={1}
          onChange={(e) => {
            setText(e.target.value)
            resize(e.target.value)
          }}
          onKeyDown={handleKeyDown}
          placeholder="Pregunta sobre ventas, inventario, clientes…"
          className="flex-1 bg-transparent resize-none outline-none text-sm text-gray-800 placeholder:text-gray-400 max-h-[140px] py-1.5"
        />

        {streaming ? (
          <button
            onClick={onStop}
            aria-label="Detener respuesta"
            className="shrink-0 p-2.5 rounded-xl bg-gray-200 hover:bg-gray-300 text-gray-700 transition-colors"
          >
            <Square className="w-4 h-4 fill-current" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!text.trim() || disabled}
            aria-label="Enviar mensaje"
            className="shrink-0 p-2.5 rounded-xl bg-emerald-900 hover:bg-emerald-800 text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>
      <p className="hidden md:block text-[11px] text-gray-400 mt-1.5 px-1">
        Enter envía · Shift+Enter salto de línea · Las respuestas se basan solo en los datos de Shaya
      </p>
    </div>
  )
}
