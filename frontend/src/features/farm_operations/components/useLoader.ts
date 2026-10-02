import { useEffect, useState } from 'react'

interface LoaderState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

/**
 * Carga datos de la API para una página o sección.
 *
 * `load` debe ser estable (envuélvelo en `useCallback` con sus
 * dependencias): cuando cambia, se vuelve a cargar. `reload` repite la
 * carga sin vaciar los datos visibles, para que la pantalla no parpadee.
 */
export function useLoader<T>(load: () => Promise<T>) {
  const [state, setState] = useState<LoaderState<T>>({ data: null, error: null, loading: true })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    load()
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            data: null,
            error: err instanceof Error ? err.message : 'Error cargando los datos',
            loading: false,
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [load, version])

  const reload = () => setVersion((current) => current + 1)

  return { ...state, reload }
}
