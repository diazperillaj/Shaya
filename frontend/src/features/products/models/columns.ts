// src/features/Farmers/columns.ts
import type { ColumnDef } from '@tanstack/react-table'
import type { Product, ProductExpense } from './types'
import { PRODUCT_EXPENSE_CATEGORY_LABELS } from './fields'

const fmtCOP = (n: number | null | undefined): string => {
  if (typeof n !== 'number' || Number.isNaN(n)) return '$ 0'
  return n.toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  })
}

/**
 * Definición de las columnas de la tabla de caficultores.
 *
 * Este arreglo describe cómo se deben mostrar los datos
 * del modelo `Product` dentro de la tabla.
 *
 * Es consumido por el componente `DataTable`, que se encarga
 * de renderizar las filas y manejar acciones como edición.
 */
export const ProductColumns: ColumnDef<Product>[] = [

  /** Identificador único del caficultor */
  {
    accessorKey: 'id',
    header: 'ID',
    cell: info => info.getValue(),
  },

  /** Nombre completo del caficultor */
  {
    accessorKey: 'name',
    header: 'Nombre',
    cell: info => info.getValue(),
  },

  /** Cantidad */
  {
    accessorKey: 'quantity',
    header: 'Cantidad',
    cell: info => info.getValue(),
  },

  /** Descripción */
  {
    accessorKey: 'description',
    header: 'Descripción',
    cell: info => info.getValue(),
  },

  /**
   * Columna de acciones.
   *
   * El contenido se renderiza dinámicamente
   * desde el componente `DataTable` mediante
   * callbacks como `onEdit`.
   */
  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]

/**
 * Columnas de la tabla de costos de producción por producto
 * (empaque, etiqueta, etc.), mostrada dentro del modal de costos.
 */
export const ProductExpenseColumns: ColumnDef<ProductExpense>[] = [
  {
    accessorKey: 'category',
    header: 'Categoría',
    cell: ({ getValue }) =>
      PRODUCT_EXPENSE_CATEGORY_LABELS[getValue() as string] ?? (getValue() as string),
  },
  {
    accessorKey: 'amount',
    header: 'Valor por bolsa',
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
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]
