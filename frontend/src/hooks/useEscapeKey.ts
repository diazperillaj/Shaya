import { useEffect, useRef } from 'react'

/**
 * Cierra un diálogo con Escape, como cualquier ventana del sistema.
 * Guarda la última función recibida: no hace falta memorizarla.
 */
export function useEscapeKey(onEscape: () => void): void {
  const handler = useRef(onEscape)
  useEffect(() => {
    handler.current = onEscape
  })
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handler.current()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
}
