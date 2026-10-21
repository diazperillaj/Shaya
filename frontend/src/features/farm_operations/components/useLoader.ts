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
 * carga sin vaciar los datos visibles, para que la pantalla no parpadee;
 * mientras tanto `refreshing` indica que hay datos y llegan otros nuevos.
 */
export function useLoader<T>(load: () => Promise<T>) {
  const [state, setState] = useState<LoaderState<T>>({ data: null, error: null, loading: true })
  const [version, setVersion] = useState(0)

  // Cambió lo que se carga (otra finca, otro periodo): se marca al momento
  const [current, setCurrent] = useState<() => Promise<T>>(() => load)
  if (current !== load) {
    setCurrent(() => load)
    setState((prev) => ({ ...prev, loading: true }))
  }

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

  const reload = () => {
    setState((prev) => ({ ...prev, loading: true }))
    setVersion((value) => value + 1)
  }

  return { ...state, refreshing: state.loading && state.data !== null, reload }
}
