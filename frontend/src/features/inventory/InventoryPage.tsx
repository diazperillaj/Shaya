import { useEffect, useState } from "react";
import DataTable from "../../components/ui/DataTable";
import Modal from "../../components/ui/Modal";
import { CirclePlus, Search, Clipboard } from "lucide-react";

import { runWithAlert } from "../../hooks/useSafeAction";

import { InventoryColumns } from "./models/columns";
import { InventoryFields, InventoryEditFields } from "./models/fields";
import type { Inventory } from "./models/types";
import {
  fetchInventorys,
  createInventory,
  updateInventory,
  deleteInventory,
  getFarmers,
} from "./services/inventory.api";

import { useAuth } from "../auth/AuthContext";

/**
 * Tipo de la función encargada de cambiar
 * el item activo del menú.
 */
type setActiveMenuItem = (item: number) => void;

/**
 * Props del componente Sidebar.
 */
interface SidebarProps {
  /** Callback para cambiar la vista activa del menú */
  setActiveMenuItem: setActiveMenuItem;
}

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
export default function InventorysPage(_props: SidebarProps) {
  /**
   * Lista de clientees obtenida desde la API.
   */
  const [data, setData] = useState<Inventory[]>([]);

  /**
   * Cliente actualmente seleccionado para edición.
   */
  const [editingInventory, setEditingInventory] = useState<Inventory | null>(
    null,
  );

  /**
   * Controla la visibilidad del modal de creación.
   */
  const [addingInventory, setAddingInventory] = useState(false);

  /**
   * Nombre base utilizado en los títulos de los modales.
   */
  const [namePage] = useState("inventario");

  /**
   * Texto de búsqueda para filtrar clientes.
   */
  const [search, setSearch] = useState("");

  /**
   * Estado reservado para futuros filtros.
   * (Actualmente no se utiliza en la consulta).
   */
  const [role] = useState("");

  /**
   * Carga la lista de cliente desde la API
   * aplicando los filtros activos.
   */
  const loadInventorys = async (): Promise<void> => {
    const Inventorys = await fetchInventorys({ search });
    setData(Inventorys);
  };

  /**
   * Usuario autenticado actual.
   * Se utiliza para validar permisos.
   */
  const { user } = useAuth();

  /**
   * Recarga la lista de clientes cada vez
   * que cambian los filtros.
   */
  useEffect(() => {
    loadInventorys();
  }, [search, role]);

  const [fields, setFields] = useState(InventoryFields);
  const [editFields, setEditFields] = useState(InventoryEditFields);

  useEffect(() => {
    const loadFarmers = async () => {
      const farmers = await getFarmers();

      const farmerOptions = [{ label: "Seleccionar", value: "" }, ...farmers];

      setFields((prev) =>
        prev.map((f) =>
          f.accessor === "farmer" ? { ...f, options: farmerOptions } : f,
        ),
      );

      setEditFields((prev) =>
        prev.map((f) =>
          f.accessor === "farmer" ? { ...f, options: farmerOptions } : f,
        ),
      );
    };

    loadFarmers();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-100 rounded-xl">
            <Clipboard className="w-6 h-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Inventario</h1>
            <p className="text-sm text-gray-400">{data.length} lote{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
        {user?.role === 'admin' && (
          <button onClick={() => setAddingInventory(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
            <CirclePlus className="w-4 h-4" /> Nuevo lote
          </button>
        )}
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar inventario…"
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
        />
      </div>
      <DataTable
        columns={InventoryColumns}
        data={data}
        onEdit={setEditingInventory}
        isAdmin={user?.role === "admin" ? true : false}
      />
      {editingInventory && (
        <Modal
          item={editingInventory}
          fields={editFields}
          onClose={() => setEditingInventory(null)}
          onSave={(Inventory) =>
            runWithAlert(async () => {
              await updateInventory(Inventory);
              await loadInventorys();
              setEditingInventory(null);
            }, "Cliente editado correctamente")
          }
          onDelete={async (id) => {
            await deleteInventory(Number(id));
            await loadInventorys();
            setEditingInventory(null);
          }}
          idKey="id"
          mode="edit"
          title={namePage}
        />
      )}

      {addingInventory && (
        <Modal
          item={{} as Inventory}
          fields={fields}
          onClose={() => setAddingInventory(false)}
          onSave={(Inventory) =>
            runWithAlert(async () => {
              await createInventory(Inventory);
              await loadInventorys();
              setAddingInventory(false);
            }, "Cliente creado correctamente")
          }
          mode="add"
          title={namePage}
        />
      )}
    </div>
  );
}
