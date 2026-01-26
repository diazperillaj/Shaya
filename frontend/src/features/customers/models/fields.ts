import type { TableField } from '../../../models/common'
import type { Customer } from './types'

/**
 * Definición de los campos del formulario de clientees.
 *
 * Este arreglo describe de forma declarativa cómo deben
 * renderizarse y vincularse los campos asociados a la
 * entidad `Customer`.
 *
 * Es utilizado por componentes genéricos (Modal, DataTable)
 * para construir formularios reutilizables sin lógica específica.
 */
export const CustomerFields: TableField<Customer>[] = [

  /** Nombre completo del cliente */
  { accessor: 'name', header: 'Nombre', type: 'text' },

  /** Documento de identificación */
  { accessor: 'document', header: 'Documento', type: 'text' },

  /**
   * Tipo de cliente asignado
   *
   * Se renderiza como un selector con valores
   * predefinidos para evitar entradas inválidas.
   */
  {
    accessor: 'customerType',
    header: 'Tipo de cliente',
    type: 'select',
    options: [
      { label: 'Minorista', value: 'Minorista' },
      { label: 'Mayorista', value: 'Mayorista' },
    ],
  },

  /** Direccion del cliente */
  { accessor: 'address', header: 'Direccion', type: 'text' },

  /** Ciudad del cliente */
  { accessor: 'city', header: 'Ciudad', type: 'text' },

  /** Correo electrónico */
  { accessor: 'email', header: 'Correo', type: 'text' },

  /** Teléfono de contacto */
  { accessor: 'phone', header: 'Teléfono', type: 'text' },

  /** Observaciones adicionales del cliente */
  { accessor: 'observation', header: 'Observación', type: 'textarea' },
]
