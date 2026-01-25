import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Funnel, ChevronDown, Search, X } from 'lucide-react';

import { runWithAlert } from '../../hooks/useSafeAction';

import { userColumns } from './models/columns'
import { userFields } from './models/fields'
import type { User } from './models/types'
import { fetchUsers, createUser, updateUser, deleteUser } from './services/user.api'

import { useAuth } from '../auth/AuthContext'

/**
 * Página de gestión de usuarios.
 *
 * Muestra la lista de usuarios registrados y permite:
 * - Buscar usuarios por texto
 * - Filtrar por rol
 * - Crear nuevos usuarios
 * - Editar usuarios existentes
 * - Eliminar usuarios
 *
 * Las acciones de edición y eliminación están disponibles
 * únicamente para usuarios con rol administrador.
 */


export default function UsersPage() {

    /**
     * Lista de usuarios obtenida desde la API.
     */
    const [data, setData] = useState<User[]>([])

    /**
     * Usuario seleccionado para la edicion
     * Si es null el modal no se muestra.
     */
    const [editingUser, setEditingUser] = useState<User | null>(null)

    /**
     * Controla la visibilidad del modal para la adicion de usuarios.
     */
    const [addingUser, setAddingUser] = useState(false)

    /**
     * Nombre de la pagina en la que se encuentra.
     */
    const [namePage] = useState('usuario')

    /**
     * Texto de busqueda para filtrar los usuarios.
     */
    const [search, setSearch] = useState('')

    /**
     * Seleccion de busqueda por rol para filtrar usuarios.
     */
    const [role, setRole] = useState('')

    /**
     * Carga los usuarios desde la API aplicando filtros si los lleva.
     */
    const loadUsers = async () => {
        const users = await fetchUsers({ search, role })
        setData(users)
    }

    /**
     * El usuario actual, se usa para validad si el usuario lleva permisos de
     * administrador.
     */
    const { user } = useAuth()

    /**
     * Efecto que recarga la lista de los usuarios
     * cada vez que se cambia un filtro por busqueda o rol.
     */
    useEffect(() => {
        loadUsers()
    }, [search, role])

    return (
        <div className="flex flex-col gap-6">
            <div className="text-3xl font-semibold flex items-center gap-2">
                <div className='flex justify-center items-center hover:cursor-pointer hover:scale-105 transition-transform duration-400'>
                    <CirclePlus onClick={() => setAddingUser(true)} className="inline w-8 h-8 text-emerald-900 font-bold" />
                </div>
                Gestión de usuarios
            </div>

            {/* Filtros */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex flex-wrap gap-4 items-end">
                    {/* Campo de búsqueda */}
                    <div className="flex-1 min-w-[200px]">
                        <label className="flex text-sm font-semibold text-gray-700 mb-2">
                            Buscar usuario
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

                    {/* Select de Rol */}
                    <div className="flex-1 min-w-[180px]">
                        <label className="flex text-sm font-semibold text-gray-700 mb-2">
                            Rol
                        </label>
                        <div className="relative">
                            <select
                                value={role} // 🔹 conectamos al estado
                                onChange={(e) => setRole(e.target.value)}
                                className="text-sm w-full border border-gray-200 rounded-xl px-4 py-3 pr-10 appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-900 focus:border-transparent transition-all duration-200 hover:border-emerald-900 bg-white cursor-pointer"
                            >
                                <option value="">Todos los roles</option>
                                <option value="admin">Administrador</option>
                                <option value="user">Usuario</option>
                            </select>
                            <div>
                                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Botones */}
                    <div className="flex gap-2 flex-col md:flex-row w-max">
                        <button
                            onClick={loadUsers} // 🔹 botón Filtrar recarga los datos
                            className="text-sm h-11 bg-emerald-900 hover:bg-emerald-950 text-white px-6 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
                        >
                            <Funnel className="w-5 h-5" />
                            Filtrar
                        </button>

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
                columns={userColumns}
                data={data}
                onEdit={setEditingUser}
                isAdmin={user?.role === 'admin' ? true : false}

            />

            {editingUser && (
                <Modal
                    item={editingUser}
                    fields={userFields}
                    onClose={() => setEditingUser(null)}
                    onSave={(user) =>
                        runWithAlert(
                            async () => {
                                await updateUser(user)
                                await loadUsers()
                                setEditingUser(null)
                            },
                            'Usuario editado correctamente'
                        )
                    }
                    onDelete={async (id) => {
                        await deleteUser(Number(id))
                        await loadUsers()
                        setEditingUser(null)
                    }}
                    idKey="id"
                    mode="edit"
                    title={namePage}
                />
            )}

            {addingUser && (
                <Modal
                    item={{} as User}
                    fields={userFields}
                    onClose={() => setAddingUser(false)}
                    onSave={(user) =>
                        runWithAlert(
                            async () => {
                                await createUser(user)
                                await loadUsers()
                                setAddingUser(false)
                            },
                            'Usuario creado correctamente'
                        )
                    }
                    mode="add"
                    title={namePage}
                />
            )}
        </div>
    )
}