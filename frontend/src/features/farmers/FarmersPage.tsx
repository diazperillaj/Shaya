import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Funnel, Search, X } from 'lucide-react'

import { runWithAlert } from '../../hooks/useSafeAction'

import { FarmerColumns } from './models/columns'
import { FarmerFields } from './models/fields'
import type { Farmer } from './models/types'
import {
  fetchFarmers,
  createFarmer,
  updateFarmer,
  deleteFarmer,
} from './services/farmer.api'

import { useAuth } from '../auth/AuthContext'

/**
 * Página de gestión de caficultores.
 *
 * Permite:
 * - Listar caficultores
 * - Buscar caficultores por texto
 * - Crear nuevos caficultores
 * - Editar caficultores existentes
 * - Eliminar caficultores
 *
 * Las acciones de edición y eliminación
 * dependen de los permisos del usuario autenticado.
 */
export default function FarmersPage() {

  /**
   * Lista de caficultores obtenida desde la API.
   */
  const [data, setData] = useState<Farmer[]>([])

  /**
   * Caficultor actualmente seleccionado para edición.
   */
  const [editingFarmer, setEditingFarmer] = useState<Farmer | null>(null)

  /**
   * Controla la visibilidad del modal de creación.
   */
  const [addingFarmer, setAddingFarmer] = useState(false)

  /**
   * Nombre base utilizado en los títulos de los modales.
   */
  const [namePage] = useState('caficultor')

  /**
   * Texto de búsqueda para filtrar caficultores.
   */
  const [search, setSearch] = useState('')

  /**
   * Estado reservado para futuros filtros.
   * (Actualmente no se utiliza en la consulta).
   */
  const [role, setRole] = useState('')

  /**
   * Carga la lista de caficultores desde la API
   * aplicando los filtros activos.
   */
  const loadFarmers = async (): Promise<void> => {
    const farmers = await fetchFarmers({ search })
    setData(farmers)
  }

  /**
   * Usuario autenticado actual.
   * Se utiliza para validar permisos.
   */
  const { user } = useAuth()

  /**
   * Recarga la lista de caficultores cada vez
   * que cambian los filtros.
   */
  useEffect(() => {
    loadFarmers()
  }, [search, role])

    return (
        <div className="flex flex-col gap-6">
            <div className="text-3xl font-semibold flex items-center gap-2">
                <div className='flex justify-center items-center hover:cursor-pointer hover:scale-105 transition-transform duration-400'>
                    <CirclePlus onClick={() => setAddingFarmer(true)} className="inline w-8 h-8 text-emerald-900 font-bold" />
                </div>
                Gestión de caficultores
            </div>

            {/* Filtros */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex flex-wrap gap-4 items-end">
                    {/* Campo de búsqueda */}
                    <div className="flex-1 min-w-[200px]">
                        <label className="flex text-sm font-semibold text-gray-700 mb-2">
                            Buscar caficultor
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
                        <button
                            onClick={loadFarmers} // 🔹 botón Filtrar recarga los datos
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
                columns={FarmerColumns}
                data={data}
                onEdit={setEditingFarmer}
                isAdmin={user?.role === 'admin' ? true : false}

            />

            {editingFarmer && (
                <Modal
                    item={editingFarmer}
                    fields={FarmerFields}
                    onClose={() => setEditingFarmer(null)}
                    onSave={(Farmer) =>
                        runWithAlert(
                            async () => {
                                await updateFarmer(Farmer)
                                await loadFarmers()
                                setEditingFarmer(null)
                            },
                            'Caficultor editado correctamente'
                        )
                    }
                    onDelete={async (id) => {
                        await deleteFarmer(Number(id))
                        await loadFarmers()
                        setEditingFarmer(null)
                    }}
                    idKey="id"
                    mode="edit"
                    title={namePage}
                />
            )}

            {addingFarmer && (
                <Modal
                    item={{} as Farmer}
                    fields={FarmerFields}
                    onClose={() => setAddingFarmer(false)}
                    onSave={(Farmer) =>
                        runWithAlert(
                            async () => {
                                await createFarmer(Farmer)
                                await loadFarmers()
                                setAddingFarmer(false)
                            },
                            'Caficultor creado correctamente'
                        )
                    }
                    mode="add"
                    title={namePage}
                />
            )}
        </div>
    )
}