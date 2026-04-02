// src/features/Customers/columns.ts
import type { ColumnDef } from '@tanstack/react-table'
import type { Customer } from './types'

/**
 * Definición de las columnas de la tabla de clientes.
 *
 * Este arreglo describe cómo se deben mostrar los datos
 * del modelo `Customer` dentro de la tabla.
 *
 * Es consumido por el componente `DataTable`, que se encarga
 * de renderizar las filas y manejar acciones como edición.
 */
export const CustomerColumns: ColumnDef<Customer>[] = [

  /** Identificador único del cliente */
  {
    accessorKey: 'id',
    header: 'ID',
    cell: info => info.getValue(),
  },

  /** Nombre completo del cliente */
  {
    accessorKey: 'name',
    header: 'Nombre',
    cell: info => info.getValue(),
  },

  /** Documento de identificación */
  {
    accessorKey: 'document',
    header: 'Documento',
    cell: info => info.getValue(),
  },

  /** Teléfono de contacto */
  {
    accessorKey: 'phone',
    header: 'Teléfono',
    cell: info => info.getValue(),
  },

  /** Correo electrónico */
  {
    accessorKey: 'email',
    header: 'Correo',
    cell: info => info.getValue(),
  },

  /** Tipo de cliente */
  {
    accessorKey: 'customerType',
    header: 'Tipo de cliente',
    cell: info => info.getValue(),
  },

  /** Direccion del cliente */
  {
    accessorKey: 'address',
    header: 'Direccion',
    cell: info => info.getValue(),
  },

    /** Ciudad del cliente */
  {
    accessorKey: 'city',
    header: 'Ciudad',
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
