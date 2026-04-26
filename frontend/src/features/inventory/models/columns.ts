// src/features/Inventorys/columns.ts
import type { ColumnDef } from '@tanstack/react-table'
import type { Inventory } from './types'

/**
 * Definición de las columnas de la tabla de clientes.
 *
 * Este arreglo describe cómo se deben mostrar los datos
 * del modelo `Inventory` dentro de la tabla.
 *
 * Es consumido por el componente `DataTable`, que se encarga
 * de renderizar las filas y manejar acciones como edición.
 */
export const InventoryColumns: ColumnDef<Inventory>[] = [

  {
    accessorKey: 'id',
    header: 'ID',
  },

  {
    accessorKey: 'farmer',
    header: 'Caficultor',
    cell: ({ row }) => row.original.farmer.person.full_name,
  },

  {
    accessorKey: 'variety',
    header: 'Variedad',
  },

  {
    accessorKey: 'elevation',
    header: 'Altitud (m.s.n.m)',
  },

  {
    accessorKey: 'humidity',
    header: 'Humedad (%)',
  },

  {
    accessorKey: 'price',
    header: 'Precio de compra',
  },

  {
    accessorKey: 'full_price',
    header: 'Precio por carga ',
  },

  {
    accessorKey: 'quantity',
    header: 'Cantidad inicial (Kg)',
  },

  {
    accessorKey: 'remaining_quantity',
    header: 'Cantidad restante (Kg)',
  },

  {
    accessorKey: 'date',
    header: 'Fecha de compra',
  },

  {
    accessorKey: 'observation',
    header: 'Observaciones',
  },

  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]