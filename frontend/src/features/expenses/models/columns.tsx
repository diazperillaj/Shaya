import type { ColumnDef } from '@tanstack/react-table'
import type { GeneralExpense } from './types'

const fmtCOP = (n: number | null | undefined): string => {
  if (typeof n !== 'number' || Number.isNaN(n)) return '$ 0'
  return n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}

export const ExpenseColumns: ColumnDef<GeneralExpense>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },

  {
    accessorKey: 'expense_date',
    header: 'Fecha',
  },

  {
    accessorKey: 'category_name',
    header: 'Categoría',
    cell: ({ getValue }) => (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border bg-emerald-100 text-emerald-800 border-emerald-200">
        {getValue() as string}
      </span>
    ),
  },

  {
    accessorKey: 'description',
    header: 'Motivo',
  },

  {
    accessorKey: 'payment_method_name',
    header: 'Pagado con',
  },

  {
    accessorKey: 'amount',
    header: 'Valor',
    cell: ({ getValue }) => (
      <span className="font-semibold text-red-700">{fmtCOP(getValue() as number)}</span>
    ),
  },

  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]
