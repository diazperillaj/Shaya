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
  initialPageSize?: number
}

export default function DataTable<T>({
  data,
  columns,
  onEdit,
  initialPageSize = 30,
}: DataTableProps<T>) {
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: initialPageSize })
  const [sorting, setSorting] = useState<any[]>([])

  const table = useReactTable({
    data,
    columns,
    state: { pagination, sorting },
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className="px-6 py-4 text-center text-sm font-medium text-white uppercase tracking-wider cursor-pointer select-none"
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
            {table.getRowModel().rows.map((row, index) => (
              <tr
                key={row.id}
                className={`transition-all duration-200 hover:bg-emerald-50/50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
                  }`}
              >
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-6 p-1 text-sm text-gray-700">
                    {cell.column.id === 'edit' && onEdit ? (
                      <button
                        className="bg-emerald-900 hover:from-emerald-500 hover:to-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
                        onClick={() => onEdit(row.original)}
                      >
                        Editar
                      </button>
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

      {/* Paginación */}
      <div className="flex justify-between items-center px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100 border-t border-gray-200">
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
    </div>
  )
}
