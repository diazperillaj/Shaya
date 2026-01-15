// src/components/ui/DataTable.tsx
import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import type { ColumnDef } from '@tanstack/react-table';

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T, any>[];
  onEdit?: (item: T) => void;
}

export default function DataTable<T>({ data, columns, onEdit }: DataTableProps<T>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-100">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th 
                    data-id={header.id}
                    key={header.id} 
                    className="px-6 py-4 text-center text-sm font-medium text-white uppercase tracking-wider"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {table.getRowModel().rows.map((row, index) => (
              <tr 
                key={row.id} 
                className={`transition-all duration-200 hover:bg-emerald-50/50 ${
                  index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
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
    </div>
  );
}