// src/features/users/columns.ts
import type { ColumnDef } from '@tanstack/react-table';
import type { User } from './types';

export const userColumns: ColumnDef<User>[] = [
  {
    accessorKey: 'nombre',
    header: 'Nombre',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'usuario',
    header: 'Usuario',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'correo',
    header: 'Correo',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'telefono',
    header: 'Teléfono',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'rol',
    header: 'Rol',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null, // Lo manejamos en DataTable con onEdit
  },
];
