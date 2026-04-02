// src/features/users/columns.ts
import type { ColumnDef } from '@tanstack/react-table'
import type { User } from './types'

/**
 * Definición de las columnas de la tabla de usuarios.
 *
 * Este arreglo describe cómo se deben renderizar los datos
 * del modelo `User` dentro de la tabla.
 *
 * Es consumido por el componente `DataTable`, que se encarga
 * de:
 * - Renderizar los encabezados
 * - Mostrar los valores de cada fila
 * - Gestionar acciones como edición
 */
export const userColumns: ColumnDef<User>[] = [

  /** Identificador único del usuario */
  {
    accessorKey: 'id',
    header: 'ID',
    cell: info => info.getValue(),
  },

  /** Nombre completo del usuario */
  {
    accessorKey: 'name',
    header: 'Nombre',
    cell: info => info.getValue(),
  },

  /** Nombre de usuario para autenticación */
  {
    accessorKey: 'username',
    header: 'Usuario',
    cell: info => info.getValue(),
  },

  /** Correo electrónico del usuario */
  {
    accessorKey: 'email',
    header: 'Correo',
    cell: info => info.getValue(),
  },

  /** Teléfono de contacto */
  {
    accessorKey: 'phone',
    header: 'Teléfono',
    cell: info => info.getValue(),
  },

  /** Rol asignado al usuario dentro del sistema */
  {
    accessorKey: 'role',
    header: 'Rol',
    cell: info => info.getValue(),
  },

  /** Observaciones adicionales del usuario */
  {
    accessorKey: 'observation',
    header: 'Observaciones',
    cell: info => info.getValue(),
  },

  /**
   * Columna de acciones.
   *
   * El contenido se renderiza dinámicamente
   * desde el componente `DataTable`, utilizando
   * callbacks como `onEdit`.
   */
  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null,
  },
]
