import type { TableField } from '../../../models/common'
import type { User } from './types'

export const userFields: TableField<User>[] = [
  { accessor: 'name', header: 'Nombre', type: 'text' },
  { accessor: 'document', header: 'Documento', type: 'text' },
  { accessor: 'username', header: 'Usuario', type: 'text' },
  { accessor: 'password', header: 'Contraseña', type: 'password' },
  { accessor: 'email', header: 'Correo', type: 'text' },
  { accessor: 'phone', header: 'Teléfono', type: 'text' },
  {
    accessor: 'role',
    header: 'Rol',
    type: 'select',
    options: [
      { label: 'Usuario', value: 'user' },
      { label: 'Administrador', value: 'admin' },
    ],
  },
  { accessor: 'observation', header: 'Observación', type: 'textarea' },
]
