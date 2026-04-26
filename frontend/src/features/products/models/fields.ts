import type { TableField } from '../../../models/common'
import type { Product } from './types'

/**
 * Definición de los campos del formulario de productos.
 *
 * Este arreglo describe de forma declarativa cómo deben
 * renderizarse y vincularse los campos asociados a la
 * entidad `Product`.
 *
 * Es utilizado por componentes genéricos (Modal, DataTable)
 * para construir formularios reutilizables sin lógica específica.
 */
export const ProductFields: TableField<Product>[] = [
  /** Nombre del producto */
  { accessor: 'name', header: 'Nombre', type: 'text' },

  /** Cantidad del producto */
  { accessor: 'quantity', header: 'Cantidad', type: 'number' },

  /** * Tipo de producto. 
   * Nota: Si tu componente genérico lo soporta, el tipo 'select' es ideal aquí. 
   * Es posible que necesites agregar una propiedad `options` dependiendo de cómo 
   * esté definida tu interfaz `TableField`.
   */
  {
    accessor: 'type',
    header: 'Tipo',
    type: 'select',
    options: [
      { label: 'Procesado', value: 'processed' },
      { label: 'Parchment', value: 'parchment' },
      { label: 'Otro', value: 'other' },
    ],
  },

  /** Descripción adicional del producto */
  { accessor: 'description', header: 'Descripción', type: 'textarea' },
]