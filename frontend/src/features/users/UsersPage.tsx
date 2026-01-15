// src/features/users/UsersPage.tsx
import { useState } from 'react';
import DataTable from '../../components/ui/DataTable';
import { userColumns } from './columns';
import type { User } from './types';
import type { TableField } from '../../models/common';
import { CirclePlus, Funnel, ChevronDown, Search, X } from 'lucide-react';
import Modal from '../../components/ui/Modal';


const mockUsers: User[] = [
    { id: 1, nombre: 'Juan Perez', usuario: 'juanp', correo: 'juan@gmail.com', telefono: '123456789', rol: 'Admin' },
    { id: 2, nombre: 'Maria Gomez', usuario: 'mariag', correo: 'maria@gmail.com', telefono: '987654321', rol: 'User' },
    { id: 3, nombre: 'Carlos Rodriguez', usuario: 'carlosr', correo: 'carlos@gmail.com', telefono: '321654987', rol: 'User' },
    { id: 4, nombre: 'Ana Martinez', usuario: 'anam', correo: 'ana@gmail.com', telefono: '654987321', rol: 'Admin' },
    { id: 5, nombre: 'Luis Fernandez', usuario: 'luisf', correo: 'luis@gmail.com', telefono: '789123456', rol: 'User' },
    { id: 6, nombre: 'Laura Sanchez', usuario: 'lauras', correo: 'laura@gmail.com', telefono: '456789123', rol: 'User' },
    { id: 7, nombre: 'Miguel Torres', usuario: 'miguelt', correo: 'miguel@gmail.com', telefono: '159753486', rol: 'Admin' },
    { id: 8, nombre: 'Sofia Ramirez', usuario: 'sofiar', correo: 'sofia@gmail.com', telefono: '753159486', rol: 'User' },
    { id: 9, nombre: 'Diego Castro', usuario: 'diegoc', correo: 'diego@gmail.com', telefono: '951357486', rol: 'User' },
    { id: 10, nombre: 'Valeria Diaz', usuario: 'valeriad', correo: 'valeria@gmail.com', telefono: '258147369', rol: 'Admin' },
    { id: 11, nombre: 'Andres Morales', usuario: 'andresm', correo: 'andres@gmail.com', telefono: '357951486', rol: 'User' },
    { id: 12, nombre: 'Carolina Ruiz', usuario: 'carolinar', correo: 'carolina@gmail.com', telefono: '456123789', rol: 'User' },
    { id: 13, nombre: 'Fernando Herrera', usuario: 'fernandoh', correo: 'fernando@gmail.com', telefono: '654321987', rol: 'Admin' },
    { id: 14, nombre: 'Gabriela Jimenez', usuario: 'gabrielaj', correo: 'gabriela@gmail.com', telefono: '789456123', rol: 'User' },
    { id: 15, nombre: 'Javier Morales', usuario: 'javierm', correo: 'javier@gmail.com', telefono: '321987654', rol: 'User' },
    { id: 16, nombre: 'Natalia Castro', usuario: 'nataliac', correo: 'natalia@gmail.com', telefono: '987321654', rol: 'Admin' },
    { id: 17, nombre: 'Ricardo Ortiz', usuario: 'ricardoo', correo: 'ricardo@gmail.com', telefono: '123789456', rol: 'User' },
    { id: 18, nombre: 'Isabel Flores', usuario: 'isabelf', correo: 'isabel@gmail.com', telefono: '456987123', rol: 'User' },
    { id: 19, nombre: 'Daniela Moreno', usuario: 'danielam', correo: 'daniela@gmail.com', telefono: '789654321', rol: 'Admin' },
    { id: 20, nombre: 'Sebastian Rojas', usuario: 'sebastianr', correo: 'sebastian@gmail.com', telefono: '147258369', rol: 'User' },
    { id: 21, nombre: 'Camila Vega', usuario: 'camilav', correo: 'camila@gmail.com', telefono: '963852741', rol: 'User' },
    { id: 22, nombre: 'Mateo Alvarez', usuario: 'mateoa', correo: 'mateo@gmail.com', telefono: '258369147', rol: 'Admin' },
    { id: 23, nombre: 'Paula Medina', usuario: 'paulam', correo: 'paula@gmail.com', telefono: '741852963', rol: 'User' },
    { id: 24, nombre: 'Adrian Castillo', usuario: 'adrianc', correo: 'adrian@gmail.com', telefono: '369147258', rol: 'User' },
    { id: 25, nombre: 'Fernanda Lopez', usuario: 'fernandal', correo: 'fernanda@gmail.com', telefono: '852963741', rol: 'Admin' },
    { id: 26, nombre: 'Emiliano Gutierrez', usuario: 'emilianog', correo: 'emiliano@gmail.com', telefono: '159486753', rol: 'User' },
    { id: 27, nombre: 'Lorena Pacheco', usuario: 'lorenap', correo: 'lorena@gmail.com', telefono: '753486159', rol: 'User' },
    { id: 28, nombre: 'Tomás Molina', usuario: 'tomasm', correo: 'tomas@gmail.com', telefono: '486159753', rol: 'Admin' },
    { id: 29, nombre: 'Elena Rivas', usuario: 'elenar', correo: 'elena@gmail.com', telefono: '951486753', rol: 'User' },
    { id: 30, nombre: 'Alvaro Peña', usuario: 'alvarop', correo: 'alvaro@gmail.com', telefono: '357258951', rol: 'User' },
];

const userFields: TableField<User>[] = [
    { accessor: 'nombre', header: 'Nombre' },
    { accessor: 'usuario', header: 'Usuario' },
    { accessor: 'correo', header: 'Correo' },
    { accessor: 'telefono', header: 'Teléfono' },
    { accessor: 'rol', header: 'Rol' },
];

export default function UsersPage() {
    const [data, setData] = useState<User[]>(mockUsers);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [addingUser, setAddingUser] = useState<boolean>(false);
    const userToAdd: User = { id: 0, nombre: '', usuario: '', correo: '', telefono: '', rol: '' };


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
