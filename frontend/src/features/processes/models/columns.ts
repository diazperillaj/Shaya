// features/inventoryProcessed/models/columns.ts

import type { ColumnDef } from '@tanstack/react-table'
import type { Process, ProcessCostProduct, ProcessExpense } from './types'
import { PROCESS_EXPENSE_CATEGORY_LABELS } from './fields'

const fmtCOP = (n: number | null | undefined): string => {
  if (typeof n !== 'number' || Number.isNaN(n)) return '$ 0'
  return n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}

const fmtNumber = (n: number | null | undefined, suffix = ''): string => {
  if (typeof n !== 'number' || Number.isNaN(n)) return `0${suffix}`
  return `${n}${suffix}`
}

export const ProcessColumns: ColumnDef<Process>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },

  {
    accessorKey: 'invoice_number',
    header: 'No. Factura',
  },

  {
    accessorKey: 'process_date',
    header: 'Fecha',
  },

  {
    accessorKey: 'parchment_kg',
    header: 'Pergamino (Kg)',
    cell: ({ getValue }) => fmtNumber(getValue() as number | undefined, ' Kg'),
  },

  {
    accessorKey: 'resultant_kg',
    header: 'Resultante (Kg)',
    cell: ({ getValue }) => fmtNumber(getValue() as number | undefined, ' Kg'),
  },

  {
    accessorKey: 'yield_percentage',
    header: 'Rendimiento (%)',
    cell: ({ getValue }) => fmtNumber(getValue() as number | undefined, ' %'),
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
    accessorKey: 'observations',
    header: 'Observaciones',
    cell: ({ getValue }) => {
      const value = (getValue() as string | undefined)?.trim()
      return value ? value : 'Sin observacion'
    },
  },

  {
    // This column is handled by DataTable to render Edit + View buttons.
    // The cell renderer is overridden in InventoryProcessedPage via the
    // DataTable `extraActions` prop (or however your DataTable exposes it).
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]

// ─── Costos por producto (solo lectura, dentro del modal de detalle) ─────────

export const ProcessCostProductColumns: ColumnDef<ProcessCostProduct>[] = [
  {
    accessorKey: 'product_name',
    header: 'Producto',
    cell: ({ row }) =>
      row.original.product_name ?? `Producto #${row.original.product_id}`,
  },
  {
    accessorKey: 'bag_quantity',
    header: 'Bolsas',
    meta: { narrow: true },
  },
  {
    accessorKey: 'product_expenses_per_bag',
    header: 'Gastos prod. / bolsa',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },
  {
    accessorKey: 'unit_cost',
    header: 'Costo unitario',
    cell: ({ getValue }) => {
      const v = getValue() as number | null
      return v == null ? '—' : fmtCOP(v)
    },
  },
  {
    accessorKey: 'total_cost',
    header: 'Costo del lote',
    cell: ({ getValue }) => {
      const v = getValue() as number | null
      return v == null ? '—' : fmtCOP(v)
    },
  },
]

// ─── Gastos del proceso (con acciones, dentro del modal de detalle) ──────────

export const ProcessExpenseColumns: ColumnDef<ProcessExpense>[] = [
  {
    accessorKey: 'category',
    header: 'Categoría',
    cell: ({ getValue }) =>
      PROCESS_EXPENSE_CATEGORY_LABELS[getValue() as string] ?? (getValue() as string),
  },
  {
    accessorKey: 'amount',
    header: 'Valor',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },
  {
    accessorKey: 'expense_date',
    header: 'Fecha',
  },
  {
    accessorKey: 'observations',
    header: 'Observaciones',
    cell: ({ getValue }) => {
      const value = (getValue() as string | undefined)?.trim()
      return value ? value : 'Sin observacion'
    },
  },
  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]