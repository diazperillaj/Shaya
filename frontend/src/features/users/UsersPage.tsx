// src/features/users/UsersPage.tsx
import { useState, useEffect } from 'react';
import DataTable from '../../components/ui/DataTable';
import { userColumns } from './columns';
import type { User } from './types';
import type { TableField } from '../../models/common';
import { CirclePlus, Funnel, ChevronDown, Search, X } from 'lucide-react';
import Modal from '../../components/ui/Modal';

const userFields: TableField<User>[] = [
    { accessor: 'nombre', header: 'Nombre' },
    { accessor: 'usuario', header: 'Usuario' },
    { accessor: 'correo', header: 'Correo' },
    { accessor: 'telefono', header: 'Teléfono' },
    { accessor: 'rol', header: 'Rol' },
];

export default function UsersPage() {
    const [data, setData] = useState<User[]>([]);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [addingUser, setAddingUser] = useState<boolean>(false);
    const userToAdd: User = { id: 0, nombre: '', usuario: '', correo: '', telefono: '', rol: '' };
    const fetchUsers = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/users/get/users') // ajusta endpoint
            const result = await response.json()

            const mappedUsers: User[] = result.map((u: any) => ({
                id: u.id,
                nombre: u.person.full_name,
                usuario: u.username,
                correo: u.person.email,
                telefono: u.person.phone,
                rol: u.role,
            }))

            console.log(mappedUsers)

            setData(mappedUsers)
        } catch (error) {
            console.error('Error fetching users', error)
        }
    }

    useEffect(() => {
        fetchUsers()
    }, [])

    return (
        <div className="flex flex-col gap-6">
            <div className="text-3xl font-semibold text-gray-700 flex gap-2 items-center">
                <div className='flex justify-center items-center hover:cursor-pointer hover:scale-105 transition-transform duration-400'>
                    <CirclePlus onClick={() => setAddingUser(true)} className="inline w-8 h-8 text-emerald-900 font-bold" />
                </div>
                <h1>
                    Gestion de Usuarios
                </h1>
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


            {/* Tabla */}
            <DataTable<User>
                columns={userColumns}
                data={data}
                onEdit={(user) => setEditingUser(user)} // Abrimos el modal
            />
            {/* Modal de edición */}
            {editingUser && (
                <Modal<User>
                    item={editingUser}
                    fields={userFields}
                    onClose={() => setEditingUser(null)}
                    onSave={(updated) => {
                        setData((prev) =>
                            prev.map((u) => (u.id === updated.id ? updated : u))
                        );
                        setEditingUser(null);
                    }}
                    onDelete={(id) => {
                        setData((prev) => prev.filter((u) => u.id !== id));
                        setEditingUser(null);
                    }}
                    idKey="id"
                    mode="edit"
                />
            )}
            {
                addingUser && (
                    <Modal<User>
                        item={userToAdd}
                        fields={userFields}
                        onClose={() => setAddingUser(false)}
                        onSave={(newUser) => {
                            setData((prev) => [...prev, newUser]);
                            setAddingUser(false);
                        }}
                        idKey="id"
                        mode="add"
                    />
                )
            }
        </div>
    );
}
