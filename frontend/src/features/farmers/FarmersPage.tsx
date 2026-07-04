import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Search, PersonStanding } from 'lucide-react'

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
  const [role] = useState('')

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
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-100 rounded-xl">
                  <PersonStanding className="w-6 h-6 text-emerald-800" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Caficultores</h1>
                  <p className="text-sm text-gray-400">{data.length} caficultor{data.length !== 1 ? 'es' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
                </div>
              </div>
              {user?.role === 'admin' && (
                <button onClick={() => setAddingFarmer(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
                  <CirclePlus className="w-4 h-4" /> Nuevo caficultor
                </button>
              )}
            </div>

            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar caficultor…"
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
              />
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