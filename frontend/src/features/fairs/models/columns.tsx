import type { ColumnDef } from '@tanstack/react-table'
import type { Fair, FairStatus } from './types'
import { BarChart2, Eye } from 'lucide-react'

const fmtCOP = (n: number) =>
  n.toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })

const fmtDatetime = (iso: string) =>
  new Date(iso).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })

const statusLabel: Record<FairStatus, string> = { open: 'Abierta', closed: 'Cerrada' }
const statusColors: Record<FairStatus, string> = {
  open: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  closed: 'bg-gray-100 text-gray-700 border-gray-200',
}

export const makeFairColumns = (
  onDetail: (fair: Fair) => void,
  onReport: (fair: Fair) => void,
  onEdit: (fair: Fair) => void,
): ColumnDef<Fair>[] => [
  { accessorKey: 'id', header: 'ID' },
  { accessorKey: 'name', header: 'Nombre' },
  { accessorKey: 'location', header: 'Ubicación', cell: ({ getValue }) => (getValue() as string | undefined) ?? '—' },
  {
    accessorKey: 'startDatetime',
    header: 'Inicio',
    cell: ({ getValue }) => fmtDatetime(getValue() as string),
  },
  {
    accessorKey: 'status',
    header: 'Estado',
    cell: ({ getValue }) => {
      const s = getValue() as FairStatus
      return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusColors[s] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}>
          {statusLabel[s] ?? s}
        </span>
      )
    },
  },
  {
    accessorKey: 'totalSales',
    header: 'Ventas',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },
  {
    accessorKey: 'totalExpenses',
    header: 'Gastos',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },
  {
    accessorKey: 'netProfit',
    header: 'Ganancia',
    cell: ({ getValue }) => {
      const v = getValue() as number
      return <span className={v >= 0 ? 'text-emerald-700 font-semibold' : 'text-red-600 font-semibold'}>{fmtCOP(v)}</span>
    },
  },
  {
    id: 'actions',
    header: 'Acciones',
    cell: ({ row }) => (
      <div className="flex items-center justify-center gap-2">
        <button
          onClick={() => onEdit(row.original)}
          className="bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-1 rounded-lg text-sm font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
        >
          Editar
        </button>
        <button
          onClick={() => onDetail(row.original)}
          className="flex items-center gap-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 px-4 py-1 rounded-lg text-sm font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200"
        >
          <Eye className="w-3.5 h-3.5" /> Ver
        </button>
        <button
          onClick={() => onReport(row.original)}
          className="flex items-center gap-1 bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 px-4 py-1 rounded-lg text-sm font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200"
        >
          <BarChart2 className="w-3.5 h-3.5" /> Reporte
        </button>
      </div>
    ),
  },
]
