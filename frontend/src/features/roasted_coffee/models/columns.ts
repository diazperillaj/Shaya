// src/features/roasted_coffee/models/columns.ts
import type { ColumnDef } from '@tanstack/react-table'
import type { RoastedCoffeeRow } from './types'

export const RoastedCoffeeColumns: ColumnDef<RoastedCoffeeRow>[] = [
  {
    accessorKey: 'maquilado_id',
    header: 'ID de Maquila',
    cell: info => info.getValue(),
    meta: { narrow: true },
  },
  {
    accessorKey: 'process_id',
    header: 'ID de Proceso',
    cell: info => info.getValue(),
    meta: { narrow: true },
  },
  {
    accessorKey: 'variety',
    header: 'Variedad',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'product_name',
    header: 'Producto',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'quantity',
    header: 'Cantidad inicial',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'remaining_quantity',
    header: 'Cantidad restante',
    cell: info => info.getValue(),
  },
]
