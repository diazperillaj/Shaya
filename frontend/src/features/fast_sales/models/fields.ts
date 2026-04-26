import type { TableField } from '../../../models/common'
import type { Sale } from './types'

/**
 * Definición de los campos del formulario de ventas.
 *
 * Este arreglo describe de forma declarativa cómo deben
 * renderizarse y vincularse los campos asociados a la
 * entidad `Sale`.
 *
 * Es utilizado por componentes genéricos (Modal, DataTable)
 * para construir formularios reutilizables sin lógica específica.
 */
export const SaleFields: TableField<Sale>[] = [
  /** Producto vendido */
  { 
    accessor: 'product', 
    header: 'Producto', 
    type: "select",
    options: [],
  },

  /** Cantidad de la venta */
  { accessor: 'quantity', header: 'Cantidad', type: 'number' },

  /** Precio de la venta */
  { accessor: 'price', header: 'Precio', type: 'number' },


  /** Descripción adicional de la venta */
  { accessor: 'description', header: 'Descripción', type: 'textarea' },
]