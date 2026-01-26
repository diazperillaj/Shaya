import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Funnel, Search, X } from 'lucide-react'

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
  const [role, setRole] = useState('')

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
            <div className="text-3xl font-semibold flex items-center gap-2">
                <div className='flex justify-center items-center hover:cursor-pointer hover:scale-105 transition-transform duration-400'>
                    <CirclePlus onClick={() => setAddingCustomer(true)} className="inline w-8 h-8 text-emerald-900 font-bold" />
                </div>
                Gestión de clientes
            </div>

            {/* Filtros */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex flex-wrap gap-4 items-end">
                    {/* Campo de búsqueda */}
                    <div className="flex-1 min-w-[200px]">
                        <label className="flex text-sm font-semibold text-gray-700 mb-2">
                            Buscar cliente
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Buscar"
                                value={search} // 🔹 conectamos al estado
                                onChange={(e) => setSearch(e.target.value)}
                                className="text-sm w-full border border-gray-200 rounded-xl px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-emerald-900 focus:border-transparent transition-all duration-200 hover:border-emerald-900"
                            />
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        </div>
                    </div>

                    {/* Botones */}
                    <div className="flex gap-2 flex-col md:flex-row w-max">
                        {/* <button
                            onClick={loadCustomers} // 🔹 botón Filtrar recarga los datos
                            className="text-sm h-11 bg-emerald-900 hover:bg-emerald-950 text-white px-6 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
                        >
                            <Funnel className="w-5 h-5" />
                            Filtrar
                        </button> */}

                        <button
                            onClick={() => { setSearch(''); setRole('') }} // 🔹 Limpiar filtros
                            className="text-sm h-11 bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 flex items-center gap-2 border border-gray-200"
                        >
                            <X className="w-5 h-5" />
                            Limpiar
                        </button>
                    </div>
                </div>
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