import type { TableField } from '../../../models/common'
import type { User } from './types'

/**
 * Definición de los campos del formulario de usuarios.
 *
 * Este arreglo describe cómo deben renderizarse y manejarse
 * los campos asociados a la entidad `User` dentro de tablas
 * y modales dinámicos.
 *
 * Se utiliza principalmente por componentes genéricos
 * (DataTable, Modal) para:
 * - Renderizar inputs según su tipo
 * - Asociar campos del formulario con propiedades del modelo
 * - Centralizar la configuración del formulario
 */
export const userFields: TableField<User>[] = [

  /** Nombre completo del usuario */
  { accessor: 'name', header: 'Nombre', type: 'text' },

  /** Documento de identificación */
  { accessor: 'document', header: 'Documento', type: 'text' },

  /** Nombre de usuario para autenticación */
  { accessor: 'username', header: 'Usuario', type: 'text' },

  /**
   * Contraseña del usuario.
   *
   * Este campo se muestra únicamente en contextos
   * de creación o actualización controlada.
   */
  { accessor: 'password', header: 'Contraseña', type: 'password' },

  /** Correo electrónico del usuario */
  { accessor: 'email', header: 'Correo', type: 'text' },

  /** Teléfono de contacto */
  { accessor: 'phone', header: 'Teléfono', type: 'text' },

  /**
   * Rol asignado al usuario.
   *
   * Se renderiza como un selector con valores
   * predefinidos para evitar entradas inválidas.
   */
  {
    accessor: 'role',
    header: 'Rol',
    type: 'select',
    options: [
      { label: 'Usuario', value: 'user' },
      { label: 'Administrador', value: 'admin' },
    ],
  },

  /** Observaciones adicionales del usuario */
  { accessor: 'observation', header: 'Observación', type: 'textarea' },
]
