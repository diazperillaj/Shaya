// src/features/users/columns.ts
import type { ColumnDef } from '@tanstack/react-table';
import type { User } from './types';

export const userColumns: ColumnDef<User>[] = [
  {
    accessorKey: 'name',
    header: 'Nombre',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'username',
    header: 'Usuario',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'email',
    header: 'Correo',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'phone',
    header: 'Teléfono',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'role',
    header: 'Rol',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null, // Lo manejamos en DataTable con onEdit
  },
];
