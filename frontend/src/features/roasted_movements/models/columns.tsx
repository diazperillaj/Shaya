import type { ColumnDef } from '@tanstack/react-table'
import type { RoastedMovement } from './types'

export const movementColumns: ColumnDef<RoastedMovement, any>[] = [
  {
    accessorKey: 'id',
    header: '#',
    cell: ({ getValue }) => (
      <span className="font-mono text-xs text-gray-500">#{getValue()}</span>
    ),
  },
  {
    accessorKey: 'movement_date',
    header: 'Fecha',
    cell: ({ getValue }) => {
      const d = new Date(getValue())
      return (
        <span className="text-sm text-gray-700">
          {d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
        </span>
      )
    },
  },
  {
    accessorKey: 'observations',
    header: 'Observaciones',
    cell: ({ getValue }) => (
      <span className="text-sm text-gray-600 italic">{getValue() || '—'}</span>
    ),
  },
  {
    id: 'products_summary',
    header: 'Productos',
    cell: ({ row }) => (
      <div className="flex flex-col gap-0.5">
        {row.original.details.map((d) => (
          <span key={d.id} className="text-xs text-gray-600 flex items-center gap-1.5 justify-center">
            <span
              className={`text-[10px] font-bold rounded-full px-1.5 py-0.5 ${
                d.direction === 'entry'
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-red-50 text-red-700'
              }`}
            >
              {d.direction === 'entry' ? '+' : '−'}{d.quantity}
            </span>
            {d.product_name}
            {d.created_lot && (
              <span className="text-[10px] text-amber-600 font-medium">(lote nuevo)</span>
            )}
          </span>
        ))}
      </div>
    ),
  },
  {
    id: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]
