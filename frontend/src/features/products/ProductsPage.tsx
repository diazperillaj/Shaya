import { useEffect, useState } from 'react'
import DataTable from '../../components/ui/DataTable'
import Modal from '../../components/ui/Modal'
import { CirclePlus, Search, Wheat } from 'lucide-react'

import { runWithAlert } from '../../hooks/useSafeAction'

import { ProductColumns } from './models/columns'
import { ProductFields } from './models/fields'
import type { Product } from './models/types'
import ProductExpensesModal from './components/ProductExpensesModal'
import {
  fetchProducts,
  createProduct,
  updateProduct,
  deleteProduct,
} from './services/product.api'

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
export default function ProductsPage() {

  /**
   * Lista de caficultores obtenida desde la API.
   */
  const [data, setData] = useState<Product[]>([])

  /**
   * Caficultor actualmente seleccionado para edición.
   */
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)

  /**
   * Controla la visibilidad del modal de creación.
   */
  const [addingProduct, setAddingProduct] = useState(false)

  /**
   * Producto cuyo modal de costos de producción está abierto.
   */
  const [viewingExpensesProduct, setViewingExpensesProduct] = useState<Product | null>(null)

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
  const loadProducts = async (): Promise<void> => {
    const Products = await fetchProducts({ search })
    setData(Products)
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
    loadProducts()
  }, [search, role])

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-100 rounded-xl">
                  <Wheat className="w-6 h-6 text-emerald-800" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Productos</h1>
                  <p className="text-sm text-gray-400">{data.length} producto{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
                </div>
              </div>
              {user?.role === 'admin' && (
                <button onClick={() => setAddingProduct(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
                  <CirclePlus className="w-4 h-4" /> Nuevo producto
                </button>
              )}
            </div>

            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar producto…"
                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
              />
            </div>

            <DataTable
                columns={ProductColumns}
                data={data}
                onEdit={setEditingProduct}
                onView={setViewingExpensesProduct}
                isAdmin={user?.role === 'admin' ? true : false}

            />

            {viewingExpensesProduct && (
                <ProductExpensesModal
                    product={viewingExpensesProduct}
                    onClose={() => setViewingExpensesProduct(null)}
                />
            )}

            {editingProduct && (
                <Modal
                    item={editingProduct}
                    fields={ProductFields}
                    onClose={() => setEditingProduct(null)}
                    onSave={(Product) =>
                        runWithAlert(
                            async () => {
                                await updateProduct(Product)
                                await loadProducts()
                                setEditingProduct(null)
                            },
                            'Caficultor editado correctamente'
                        )
                    }
                    onDelete={(id) =>
                        runWithAlert(
                            async () => {
                                await deleteProduct(Number(id))
                                await loadProducts()
                                setEditingProduct(null)
                            },
                            'Producto eliminado correctamente'
                        )
                    }
                    idKey="id"
                    mode="edit"
                    title={namePage}
                />
            )}

            {addingProduct && (
                <Modal
                    item={{} as Product}
                    fields={ProductFields}
                    onClose={() => setAddingProduct(false)}
                    onSave={(Product) =>
                        runWithAlert(
                            async () => {
                                await createProduct(Product)
                                await loadProducts()
                                setAddingProduct(false)
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