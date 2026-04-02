import type { TableField } from '../../../models/common'
import type { Farmer } from './types'

/**
 * Definición de los campos del formulario de caficultores.
 *
 * Este arreglo describe de forma declarativa cómo deben
 * renderizarse y vincularse los campos asociados a la
 * entidad `Farmer`.
 *
 * Es utilizado por componentes genéricos (Modal, DataTable)
 * para construir formularios reutilizables sin lógica específica.
 */
export const FarmerFields: TableField<Farmer>[] = [

  /** Nombre completo del caficultor */
  { accessor: 'name', header: 'Nombre', type: 'text' },

  /** Documento de identificación */
  { accessor: 'document', header: 'Documento', type: 'text' },

  /** Nombre de la finca */
  { accessor: 'farm_name', header: 'Finca', type: 'text' },

  /** Ubicación de la finca */
  { accessor: 'farm_location', header: 'Ubicación finca', type: 'text' },

  /** Correo electrónico */
  { accessor: 'email', header: 'Correo', type: 'text' },

  /** Teléfono de contacto */
  { accessor: 'phone', header: 'Teléfono', type: 'text' },

  /** Observaciones adicionales del caficultor */
  { accessor: 'observation', header: 'Observación', type: 'textarea' },
]
