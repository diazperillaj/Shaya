import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Search, UserCog } from 'lucide-react';

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
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-100 rounded-xl">
                  <UserCog className="w-6 h-6 text-emerald-800" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Usuarios</h1>
                  <p className="text-sm text-gray-400">{data.length} usuario{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
                </div>
              </div>
              {user?.role === 'admin' && (
                <button onClick={() => setAddingUser(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
                  <CirclePlus className="w-4 h-4" /> Nuevo usuario
                </button>
              )}
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar usuario…"
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
                />
              </div>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
              >
                <option value="">Todos los roles</option>
                <option value="admin">Administrador</option>
                <option value="user">Usuario</option>
              </select>
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