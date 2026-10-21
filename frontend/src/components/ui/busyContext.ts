import { createContext, createElement, useContext, useEffect, useState, type ReactNode } from 'react'

/** Si las tarjetas de adentro se están actualizando (ver Busy.tsx) */
export const BusyContext = createContext(false)

/** Marca como «actualizando» todas las tarjetas que hay dentro */
export function BusyScope({ busy, children }: { busy: boolean; children: ReactNode }) {
  const parent = useContext(BusyContext)
  return createElement(BusyContext.Provider, { value: parent || busy }, children)
}

export const useBusy = () => useContext(BusyContext)

/**
 * Mantiene `active` encendido al menos `min` ms: una respuesta rápida no
 * alcanza a verse y el usuario no sabría que su clic hizo algo.
 */
export function useMinDuration(active: boolean, min = 450): boolean {
  const [prev, setPrev] = useState(active)
  // La última vez que se encendió aún no cumple el mínimo
  const [pending, setPending] = useState(false)
  if (active !== prev) {
    setPrev(active)
    if (active) setPending(true)
  }

  useEffect(() => {
    if (!pending) return
    const timer = setTimeout(() => setPending(false), min)
    return () => clearTimeout(timer)
  }, [pending, min])

  return active || pending
}
