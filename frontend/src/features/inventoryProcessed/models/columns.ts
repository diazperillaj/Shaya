// features/inventoryProcessed/models/columns.ts

import type { ColumnDef } from '@tanstack/react-table'
import type { Process } from './types'

const fmtCOP = (n: number): string =>
  n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })

export const ProcessColumns: ColumnDef<Process>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },

  {
    accessorKey: 'No_Factura',
    header: 'No. Factura',
  },

  {
    accessorKey: 'Fecha',
    header: 'Fecha',
  },

  {
    accessorKey: 'Farmer_Nombre',
    header: 'Caficultor',
  },

  {
    accessorKey: 'Pergamino_Kg',
    header: 'Pergamino (Kg)',
    cell: ({ getValue }) => `${(getValue() as number).toFixed(2)} Kg`,
  },

  {
    accessorKey: 'Resultante',
    header: 'Resultante (Kg)',
    cell: ({ getValue }) => `${(getValue() as number).toFixed(2)} Kg`,
  },

  {
    accessorKey: 'Rendimiento',
    header: 'Rendimiento (%)',
    cell: ({ getValue }) => `${(getValue() as number).toFixed(1)} %`,
  },

  {
    accessorKey: 'Subtotal',
    header: 'Subtotal',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },

  {
    accessorKey: 'IVA',
    header: 'IVA',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },

  {
    accessorKey: 'Total',
    header: 'Total',
    cell: ({ getValue }) => fmtCOP(getValue() as number),
  },

  {
    accessorKey: 'Observaciones',
    header: 'Observaciones',
    cell: ({ getValue }) => (getValue() as string | undefined) ?? '—',
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