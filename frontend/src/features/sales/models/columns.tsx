import type { ColumnDef } from '@tanstack/react-table'
import type { Sale, SaleStatus } from './types'

const fmtCOP = (n: number | null | undefined): string => {
  if (typeof n !== 'number' || Number.isNaN(n)) return '$ 0'
  return n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}

const statusLabel: Record<SaleStatus, string> = {
  in_progress: 'En progreso',
  completed: 'Completada',
}

const statusColors: Record<SaleStatus, string> = {
  in_progress: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  completed: 'bg-emerald-100 text-emerald-800 border-emerald-200',
}

export const SaleColumns: ColumnDef<Sale>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },

  {
    accessorKey: 'customer_name',
    header: 'Cliente',
  },

  {
    accessorKey: 'user_name',
    header: 'Vendedor',
  },

  {
    accessorKey: 'sale_date',
    header: 'Fecha',
  },

  {
    accessorKey: 'status',
    header: 'Estado',
    cell: ({ getValue }) => {
      const status = getValue() as SaleStatus
      const label = statusLabel[status] ?? status
      const color = statusColors[status] ?? 'bg-gray-100 text-gray-700 border-gray-200'
      return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color}`}>
          {label}
        </span>
      )
    },
  },

  {
    accessorKey: 'subtotal',
    header: 'Subtotal',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },

  {
    accessorKey: 'iva',
    header: 'IVA',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },

  {
    accessorKey: 'total',
    header: 'Total',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },

  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]
