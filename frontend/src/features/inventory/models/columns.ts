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

  /** Identificador único del inventario */
  {
    accessorKey: 'id',
    header: 'ID',
    cell: info => info.getValue(),
  },

  /** Caficultor */
  {
    accessorKey: 'farmer',
    header: 'Caficultor',
    cell: info => info.getValue(),
  },

  /** Variedad del cafe */
  {
    accessorKey: 'variety',
    header: 'Variedad',
    cell: info => info.getValue(),
  },

  /** Altitud del lote */
  {
    accessorKey: 'elevation',
    header: 'Altitud',
    cell: info => info.getValue(),
  },

  /** Humedad del lote */
  {
    accessorKey: 'humidity',
    header: 'Humedad',
    cell: info => info.getValue(),
  },

  /** Factor de rendimiento del lote */
  {
    accessorKey: 'yield_factor',
    header: 'Factor de rendimiento',
    cell: info => info.getValue(),
  },

  /** Precio de compra */
  {
    accessorKey: 'price',
    header: 'Precio de compra',
    cell: info => info.getValue(),
  },

  /** Precio de compra */
  {
    accessorKey: 'full_price',
    header: 'Precio por carga',
    cell: info => info.getValue(),
  },

    /** Cantidad inicial */
  {
    accessorKey: 'quantity',
    header: 'Cantidad inicial',
    cell: info => info.getValue(),
  },

      /** Stock actual */
  {
    accessorKey: 'stock',
    header: 'Cantidad restante',
    cell: info => info.getValue(),
  },

      /** Fecha de compra */
  {
    accessorKey: 'date',
    header: 'Fecha de compra',
    cell: info => info.getValue(),
  },


  /** Observaciones adicionales del cliente */
  {
    accessorKey: 'observation',
    header: 'Observaciones',
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
