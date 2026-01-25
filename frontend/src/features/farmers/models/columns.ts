// src/features/Farmers/columns.ts
import type { ColumnDef } from '@tanstack/react-table';
import type { Farmer } from './types';

export const FarmerColumns: ColumnDef<Farmer>[] = [
  {
    accessorKey: 'id',
    header: 'id',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'name',
    header: 'Nombre',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'document',
    header: 'Documento',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'phone',
    header: 'Teléfono',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'email',
    header: 'Correo',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'farm_name',
    header: 'Finca',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'farm_location',
    header: 'Ubicación finca',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'observation',
    header: 'Observaciones',
    cell: info => info.getValue(),
  },
  {
    accessorKey: 'edit',
    header: 'Acciones',
    cell: () => null, // Lo manejamos en DataTable con onEdit
  },
];
