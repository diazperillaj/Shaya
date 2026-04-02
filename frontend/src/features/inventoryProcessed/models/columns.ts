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

    /** Parchment info */
    {
      accessorKey: 'parchment_info',
      header: 'Info lote',
      cell: info => info.getValue(),
    },

    /** Type */
    {
      accessorKey: 'type',
      header: 'Tipo',
      cell: info => info.getValue(),
    },

    /** Amount */
    {
      accessorKey: 'amount',
      header: 'Cantidad',
      cell: info => info.getValue(),
    },
    
    /** Variety */
    {
      accessorKey: 'variety',
      header: 'Variedad',
      cell: info => info.getValue(),
    },

    /** Roast level */
    {
      accessorKey: 'roast_level',
      header: 'Nivel de tostión',
      cell: info => info.getValue(),
    },

    /** Price per unity */
    {
      accessorKey: 'unity_price',
      header: 'Precio por unidad',
      cell: info => info.getValue(),
    },

    /** Total price */
    {
      accessorKey: 'total_price',
      header: 'Precio total',
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
