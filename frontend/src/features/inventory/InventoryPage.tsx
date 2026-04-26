import { useEffect, useState } from "react";
import DataTable from "../../components/ui/DataTable";
import Modal from "../../components/ui/Modal";
import { CirclePlus, Search, X, Replace } from "lucide-react";

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
export default function InventoryProcessedPage({
  setActiveMenuItem,
}: SidebarProps) {
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
  const [role, setRole] = useState("");

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
      <div className="flex flex-col gap-6">
        <div className="text-3xl font-semibold flex items-center justify-between">
          {/* Izquierda */}
          <div className="flex items-center gap-2">
            <div className="flex justify-center items-center hover:cursor-pointer hover:scale-105 transition-transform duration-400">
              <CirclePlus
                onClick={() => setAddingInventory(true)}
                className="inline w-8 h-8 text-emerald-900 font-bold"
              />
            </div>
            Gestión de inventario pergamino
          </div>

          {/* Derecha */}
          <button
            className="text-xl bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
            onClick={() => setActiveMenuItem(6)}
          >
            <Replace className="w-5 h-5" />
            Inventario de cafe procesado1
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Campo de búsqueda */}
          <div className="flex-1 min-w-[200px]">
            <label className="flex text-sm font-semibold text-gray-700 mb-2">
              Buscar inventario
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
                            onClick={loadInventorys} // 🔹 botón Filtrar recarga los datos
                            className="text-sm h-11 bg-emerald-900 hover:bg-emerald-950 text-white px-6 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
                        >
                            <Funnel className="w-5 h-5" />
                            Filtrar
                        </button> */}

            <button
              onClick={() => {
                setSearch("");
                setRole("");
              }} // 🔹 Limpiar filtros
              className="text-sm h-11 bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 flex items-center gap-2 border border-gray-200"
            >
              <X className="w-5 h-5" />
              Limpiar
            </button>
          </div>
        </div>
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
