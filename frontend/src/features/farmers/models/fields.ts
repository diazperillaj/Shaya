import type { TableField } from '../../../models/common'
import type { Farmer } from './types'

export const FarmerFields: TableField<Farmer>[] = [
  { accessor: 'name', header: 'Nombre', type: 'text' },
  { accessor: 'document', header: 'Documento', type: 'text' },
  { accessor: 'farm_name', header: 'Finca', type: 'text' },
  { accessor: 'farm_location', header: 'Ubicación finca', type: 'text' },
  { accessor: 'email', header: 'Correo', type: 'text' },
  { accessor: 'phone', header: 'Teléfono', type: 'text' },
  { accessor: 'observation', header: 'Observación', type: 'textarea' },
]
