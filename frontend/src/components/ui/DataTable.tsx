// src/components/ui/DataTable.tsx
import { useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender
} from '@tanstack/react-table'
import type { Column, ColumnDef, Row } from '@tanstack/react-table'
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from 'lucide-react';

interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T, any>[]
  onEdit?: (item: T) => void
  onView?: (item: T) => void
  onDelete?: (item: T) => void
  initialPageSize?: number
  isAdmin: boolean
  /** Oculta la barra de paginación (útil para listas cortas dentro de modales) */
  showPagination?: boolean
  /** Mensaje mostrado cuando no hay registros */
  emptyMessage?: string
}

type Align = 'left' | 'right' | 'center'

const ALIGN_CLASS: Record<Align, string> = {
  left: 'text-left',
  right: 'text-right',
  center: 'text-center',
}

const ROW_BUTTON =
  'px-3 py-1 rounded-lg text-sm font-medium transition-[transform,background-color,box-shadow] duration-150 ease-out active:scale-[0.97]'

const PAGE_BUTTON =
  'flex h-9 w-10 items-center justify-center rounded-lg bg-emerald-900 text-white shadow-sm transition-[transform,background-color,opacity] duration-150 ease-out hover:bg-emerald-800 active:scale-[0.96] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-emerald-900 disabled:active:scale-100'

export default function DataTable<T>({
  data,
  columns,
  onEdit,
  onView,
  onDelete,
  initialPageSize = 30,
  isAdmin = false,
  showPagination = true,
  emptyMessage = 'Sin registros'
}: DataTableProps<T>) {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: initialPageSize })
  const [sorting, setSorting] = useState<any[]>([])

  // Columnas angostas (se encogen al contenido): IDs, acciones,
  // o cualquier columna marcada con meta: { narrow: true }
  const isNarrowColumn = (column: { id: string; columnDef: ColumnDef<T, any> }) =>
    column.id === 'id' ||
    column.id === 'edit' ||
    (column.columnDef.meta as { narrow?: boolean } | undefined)?.narrow === true

  const visibleColumns = isAdmin
    ? columns
    : columns.filter(col => col.header != 'Acciones')

  const table = useReactTable({
    data,
    columns: visibleColumns,
    state: { pagination, sorting },
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  /**
   * Alineación de cada columna: las cifras a la derecha (se comparan de un
   * vistazo), el texto a la izquierda y las acciones al centro. Se puede
   * fijar con `meta: { align }`; si no, se deduce de los valores.
   */
  const sample: Row<T>[] = table.getCoreRowModel().rows.slice(0, 25)
  const alignOf = (column: Column<T, unknown>): Align => {
    const fixed = (column.columnDef.meta as { align?: Align } | undefined)?.align
    if (fixed) return fixed
    if (column.id === 'edit') return 'center'
    const values = sample.map((row) => row.getValue(column.id)).filter((v) => v !== null && v !== undefined && v !== '')
    return values.length > 0 && values.every((v) => typeof v === 'number') ? 'right' : 'left'
  }

  return (
    <div>
      {/* Paginación (sin fondo, impresa sobre el color de la página) */}
      {showPagination && (
      <div className="flex justify-between items-center px-1 pb-3">
        <div className="text-sm font-medium text-gray-700 tabular-nums">
          Página <span className="text-emerald-900 font-semibold">{table.getState().pagination.pageIndex + 1}</span> de <span className="text-emerald-900 font-semibold">{Math.max(table.getPageCount(), 1)}</span>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            aria-label="Página anterior"
            className={PAGE_BUTTON}
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            aria-label="Página siguiente"
            className={PAGE_BUTTON}
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-200/70">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-emerald-900 dark:bg-emerald-950">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => {
                  const align = alignOf(header.column)
                  const sorted = header.column.getIsSorted()
                  const canSort = header.column.getCanSort()
                  return (
                    <th
                      key={header.id}
                      scope="col"
                      aria-sort={sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : undefined}
                      className={`py-3.5 text-xs font-semibold text-white uppercase tracking-wider select-none ${ALIGN_CLASS[align]} ${
                        isNarrowColumn(header.column) ? 'w-px whitespace-nowrap px-4' : 'px-6'
                      }`}
                    >
                      {canSort && !header.isPlaceholder ? (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          className={`inline-flex items-center gap-1 uppercase tracking-wider rounded focus-visible:outline-white/70 ${align === 'right' ? 'flex-row-reverse' : ''}`}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {sorted === 'asc' && <ChevronUp className="w-4 h-4 flex-shrink-0" />}
                          {sorted === 'desc' && <ChevronDown className="w-4 h-4 flex-shrink-0" />}
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {table.getRowModel().rows.length === 0 && (
              <tr>
                <td
                  colSpan={visibleColumns.length}
                  className="px-6 py-12 text-center text-sm text-gray-400"
                >
                  {emptyMessage}
                </td>
              </tr>
            )}
            {table.getRowModel().rows.map((row, index) => (
              <tr
                key={row.id}
                className={`transition-colors duration-150 hover:bg-emerald-50/60 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/40'
                  }`}
              >
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    className={`py-2.5 text-sm text-gray-700 align-middle ${ALIGN_CLASS[alignOf(cell.column)]} ${
                      isNarrowColumn(cell.column) ? 'w-px whitespace-nowrap px-4' : 'px-6'
                    }`}
                  >
                    {cell.column.id === 'edit' && isAdmin ? (
                      <div className="flex items-center justify-center gap-2">
                        {onEdit && (
                          <button
                            type="button"
                            className={`${ROW_BUTTON} bg-emerald-900 text-white shadow-sm hover:bg-emerald-800`}
                            onClick={() => onEdit(row.original)}
                          >
                            Editar
                          </button>
                        )}
                        {onView && (
                          <button
                            type="button"
                            className={`${ROW_BUTTON} bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100`}
                            onClick={() => onView(row.original)}
                          >
                            Ver
                          </button>
                        )}
                        {onDelete && (
                          <button
                            type="button"
                            className={`${ROW_BUTTON} bg-red-600 text-white shadow-sm hover:bg-red-700`}
                            onClick={() => onDelete(row.original)}
                          >
                            Borrar
                          </button>
                        )}
                      </div>
                    ) : (
                      flexRender(cell.column.columnDef.cell, cell.getContext())
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      </div>
    </div>
  )
}
