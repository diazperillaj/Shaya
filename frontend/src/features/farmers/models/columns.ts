// src/features/Farmers/columns.ts
import type { ColumnDef } from '@tanstack/react-table'
import type { Farmer } from './types'

/**
 * Definición de las columnas de la tabla de caficultores.
 *
 * Este arreglo describe cómo se deben mostrar los datos
 * del modelo `Farmer` dentro de la tabla.
 *
 * Es consumido por el componente `DataTable`, que se encarga
 * de renderizar las filas y manejar acciones como edición.
 */
export const FarmerColumns: ColumnDef<Farmer>[] = [

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

  /** Nombre de la finca */
  {
    accessorKey: 'farm_name',
    header: 'Finca',
    cell: info => info.getValue(),
  },

  /** Ubicación de la finca */
  {
    accessorKey: 'farm_location',
    header: 'Ubicación finca',
    cell: info => info.getValue(),
  },

  /** Observaciones adicionales del caficultor */
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
