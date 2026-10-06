import { useState } from 'react'

export const PAGE_SIZE = 10

export interface PaginationState<T> {
  /** Las filas de la página actual */
  visible: T[]
  total: number
  /** Página actual, desde 1 */
  page: number
  pages: number
  /** Posición de la primera y la última fila visibles (desde 1) */
  from: number
  to: number
  canPrev: boolean
  canNext: boolean
  prev: () => void
  next: () => void
}

/**
 * Tablas y listas del módulo: de a 10 por página, como las tablas del resto
 * de la app, para que ninguna tarjeta empuje la página hacia abajo. Si la
 * lista cambia (otro filtro, una recarga) y la página ya no existe, se
 * muestra la última.
 */
export function usePagination<T>(items: readonly T[] | null | undefined, size = PAGE_SIZE): PaginationState<T> {
  const [requested, setPage] = useState(1)
  const all = items ?? []
  const pages = Math.max(1, Math.ceil(all.length / size))
  const page = Math.min(requested, pages)
  const start = (page - 1) * size
  return {
    visible: all.slice(start, start + size),
    total: all.length,
    page,
    pages,
    from: all.length === 0 ? 0 : start + 1,
    to: Math.min(start + size, all.length),
    canPrev: page > 1,
    canNext: page < pages,
    prev: () => setPage(Math.max(1, page - 1)),
    next: () => setPage(Math.min(pages, page + 1)),
  }
}
