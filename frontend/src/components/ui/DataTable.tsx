// src/components/ui/DataTable.tsx
import { useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender
} from '@tanstack/react-table'
import type { ColumnDef } from '@tanstack/react-table'
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

  return (
    <div>
      {/* Paginación (sin fondo, impresa sobre el color de la página) */}
      {showPagination && (
      <div className="flex justify-between items-center px-1 pb-3">
        <div className="text-sm font-medium text-gray-700">
          Página <span className="text-emerald-900 font-semibold">{table.getState().pagination.pageIndex + 1}</span> de <span className="text-emerald-900 font-semibold">{table.getPageCount()}</span>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-5 py-2 bg-emerald-900 text-white rounded-lg text-sm font-medium shadow-md hover:bg-emerald-800 hover:shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:bg-emerald-900"
          >
            <ChevronLeft className="inline w-4 h-4 text-white font-bold" />
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="px-5 py-2 bg-emerald-900 text-white rounded-lg text-sm font-medium shadow-md hover:bg-emerald-800 hover:shadow-lg transform hover:scale-105 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:bg-emerald-900"
          >
            <ChevronRight className="inline w-4 h-4 text-white font-bold" />
          </button>
        </div>
      </div>
      )}

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className={`py-4 text-center text-sm font-medium text-white uppercase tracking-wider cursor-pointer select-none ${
                      isNarrowColumn(header.column) ? 'w-px whitespace-nowrap px-4' : 'px-6'
                    }`}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{
                      asc: <ChevronUp className="inline w-4 h-4 text-white font-bold" />,
                      desc: <ChevronDown className="inline w-4 h-4 text-white font-bold" />,
                    }[header.column.getIsSorted() as string] ?? null}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {table.getRowModel().rows.length === 0 && (
              <tr>
                <td
                  colSpan={visibleColumns.length}
                  className="px-6 py-10 text-center text-sm text-gray-400"
                >
                  {emptyMessage}
                </td>
              </tr>
            )}
            {table.getRowModel().rows.map((row, index) => (
              <tr
                key={row.id}
                className={`transition-all duration-200 hover:bg-emerald-50/50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
                  }`}
              >
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    className={`p-2 text-sm text-gray-700 text-center align-middle ${
                      isNarrowColumn(cell.column) ? 'w-px whitespace-nowrap px-4' : 'px-6'
                    }`}
                  >
                    {cell.column.id === 'edit' && isAdmin ? (
                      <div className="flex items-center justify-center gap-2">
                        {onEdit && (
                          <button
                            className="bg-emerald-900 hover:from-emerald-500 hover:to-emerald-600 text-white px-4 p-1 rounded-lg text-sm font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
                            onClick={() => onEdit(row.original)}
                          >
                            Editar
                          </button>
                        )}
                        {onView && (
                          <button
                            className="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 px-4 p-1 rounded-lg text-sm font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200"
                            onClick={() => onView(row.original)}
                          >
                            Ver
                          </button>
                        )}
                        {onDelete && (
                          <button
                            className="bg-red-600 hover:bg-red-700 text-white px-4 p-1 rounded-lg text-sm font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
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
