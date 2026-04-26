// src/features/Farmers/columns.ts
import type { ColumnDef } from "@tanstack/react-table";
import type { Sale } from "./types";

/**
 * Definición de las columnas de la tabla de caficultores.
 *
 * Este arreglo describe cómo se deben mostrar los datos
 * del modelo `Product` dentro de la tabla.
 *
 * Es consumido por el componente `DataTable`, que se encarga
 * de renderizar las filas y manejar acciones como edición.
 */
export const SaleColumns: ColumnDef<Sale>[] = [
  /** Identificador único del caficultor */
  {
    accessorKey: "id",
    header: "ID",
    cell: (info) => info.getValue(),
  },

  /** Nombre completo del caficultor */
  {
    accessorKey: "product",
    header: "Producto",
    cell: (info) => info.getValue(),
  },

  /** Cantidad */
  {
    accessorKey: "quantity",
    header: "Cantidad",
    cell: (info) => info.getValue(),
  },

  /** Precio */
  {
    accessorKey: "price",
    header: "Precio",
    cell: (info) => info.getValue(),
  },

  /** Quien vende */
  {
    accessorKey: "user",
    header: "Vendedor",
    cell: (info) => info.getValue(),
  },

  /** Descripción */
  {
    accessorKey: "description",
    header: "Descripción",
    cell: (info) => info.getValue(),
  },

  /**
   * Columna de acciones.
   *
   * El contenido se renderiza dinámicamente
   * desde el componente `DataTable` mediante
   * callbacks como `onEdit`.
   */
  {
    accessorKey: "edit",
    header: "Acciones",
    cell: () => null,
  },
];
