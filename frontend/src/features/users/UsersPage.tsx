import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Funnel, ChevronDown, Search, X } from 'lucide-react';

import { userColumns } from './models/columns'
import { userFields } from './models/fields'
import type { User } from './models/types'
import { fetchUsers, createUser } from './services/user.api'

export default function UsersPage() {
    const [data, setData] = useState<User[]>([])
    const [editingUser, setEditingUser] = useState<User | null>(null)
    const [addingUser, setAddingUser] = useState(false)

    useEffect(() => {
        loadUsers()
    }, [])

    const loadUsers = async () => {
        setData(await fetchUsers())
    }

    return (
        <div className="flex flex-col gap-6">
            <div className="text-3xl font-semibold flex items-center gap-2">
                <CirclePlus
                    className="cursor-pointer"
                    onClick={() => setAddingUser(true)}
                />
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
                                className="text-sm w-full border border-gray-200 rounded-xl px-4 py-3 pr-10 appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-900 focus:border-transparent transition-all duration-200 hover:border-emerald-900 bg-white cursor-pointer"
                            >
                                <option value="">Todos los roles</option>
                                <option value="administrador">Administrador</option>
                                <option value="usuario">Usuario</option>
                            </select>
                            <div>
                                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                            </div>
                        </div>
                    </div>

                    {/* Botones */}
                    <div className="flex gap-2 flex-col md:flex-row w-max">
                        <button className="text-sm h-11 bg-emerald-900 hover:bg-emerald-950 text-white px-6 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2">
                            <div>
                                <Funnel className="w-5 h-5" />
                            </div>
                            Filtrar
                        </button>

                        <button className="text-sm h-11 bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 flex items-center gap-2 border border-gray-200">
                            <div>
                                <X className="w-5 h-5" />
                            </div>
                            Limpiar
                        </button>
                    </div>
                </div>
            </div>

            <DataTable
                columns={userColumns}
                data={data}
                onEdit={setEditingUser}
            />

            {editingUser && (
                <Modal
                    item={editingUser}
                    fields={userFields}
                    onClose={() => setEditingUser(null)}
                    onSave={(u) =>
                        setData(prev => prev.map(x => (x.id === u.id ? u : x)))
                    }
                    onDelete={(id) => {
                        setData((prev) => prev.filter((u) => u.id !== id));
                        setEditingUser(null);
                    }}
                    idKey="id"
                    mode="edit"
                />
            )}

            {addingUser && (
                <Modal
                    item={{} as User}
                    fields={userFields}
                    onClose={() => setAddingUser(false)}
                    onSave={async (user) => {
                        await createUser(user)
                        await loadUsers() // 🔥 REUTILIZAS
                        setAddingUser(false)
                    }}
                    mode="add"
                />
            )}
        </div>
    )
}
