import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Search, Users as UsersIcon } from 'lucide-react'

import { runWithAlert } from '../../hooks/useSafeAction'

import { CustomerColumns } from './models/columns'
import { CustomerFields } from './models/fields'
import type { Customer } from './models/types'
import {
  fetchCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
} from './services/customer.api'

import { useAuth } from '../auth/AuthContext'

/**
 * Página de gestión de clientes.
 *
 * Permite:
 * - Listar clientees
 * - Buscar clientees por texto
 * - Crear nuevos clientees
 * - Editar clientees existentes
 * - Eliminar clientees
 *
 * Las acciones de edición y eliminación
 * dependen de los permisos del usuario autenticado.
 */
export default function CustomersPage() {

  /**
   * Lista de clientees obtenida desde la API.
   */
  const [data, setData] = useState<Customer[]>([])

  /**
   * Cliente actualmente seleccionado para edición.
   */
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)

  /**
   * Controla la visibilidad del modal de creación.
   */
  const [addingCustomer, setAddingCustomer] = useState(false)

  /**
   * Nombre base utilizado en los títulos de los modales.
   */
  const [namePage] = useState('cliente')

  /**
   * Texto de búsqueda para filtrar clientes.
   */
  const [search, setSearch] = useState('')

  /**
   * Estado reservado para futuros filtros.
   * (Actualmente no se utiliza en la consulta).
   */
  const [role] = useState('')

  /**
   * Carga la lista de cliente desde la API
   * aplicando los filtros activos.
   */
  const loadCustomers = async (): Promise<void> => {
    const customers = await fetchCustomers({ search })
    setData(customers)
  }

  /**
   * Usuario autenticado actual.
   * Se utiliza para validar permisos.
   */
  const { user } = useAuth()

  /**
   * Recarga la lista de clientes cada vez
   * que cambian los filtros.
   */
  useEffect(() => {
    loadCustomers()
  }, [search, role])

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-100 rounded-xl">
                  <UsersIcon className="w-6 h-6 text-emerald-800" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
                  <p className="text-sm text-gray-400">{data.length} cliente{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
                </div>
              </div>
              {user?.role === 'admin' && (
                <button onClick={() => setAddingCustomer(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
                  <CirclePlus className="w-4 h-4" /> Nuevo cliente
                </button>
              )}
            </div>

            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar cliente…"
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
              />
            </div>

            <DataTable
                columns={CustomerColumns}
                data={data}
                onEdit={setEditingCustomer}
                isAdmin={user?.role === 'admin' ? true : false}

            />

            {editingCustomer && (
                <Modal
                    item={editingCustomer}
                    fields={CustomerFields}
                    onClose={() => setEditingCustomer(null)}
                    onSave={(Customer) =>
                        runWithAlert(
                            async () => {
                                await updateCustomer(Customer)
                                await loadCustomers()
                                setEditingCustomer(null)
                            },
                            'Cliente editado correctamente'
                        )
                    }
                    onDelete={async (id) => {
                        await deleteCustomer(Number(id))
                        await loadCustomers()
                        setEditingCustomer(null)
                    }}
                    idKey="id"
                    mode="edit"
                    title={namePage}
                />
            )}

            {addingCustomer && (
                <Modal
                    item={{} as Customer}
                    fields={CustomerFields}
                    onClose={() => setAddingCustomer(false)}
                    onSave={(Customer) =>
                        runWithAlert(
                            async () => {
                                await createCustomer(Customer)
                                await loadCustomers()
                                setAddingCustomer(false)
                            },
                            'Cliente creado correctamente'
                        )
                    }
                    mode="add"
                    title={namePage}
                />
            )}
        </div>
    )
}