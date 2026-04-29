// features/inventoryProcessed/InventoryProcessedPage.tsx

import { useEffect, useState } from "react";
import { CirclePlus, Search, X, Replace, Eye } from "lucide-react";


import { runWithAlert } from "../../hooks/useSafeAction";

import { ProcessColumns } from "./models/columns";
import type {
  Process,
  ProcessDetail,
  CreateProcessPayload,
} from "./models/types";
import {
  fetchProcesos,
  createProceso,
  fetchDetallesByProceso,
  fetchParchments,
  fetchProducts,
  
} from "./services/inventoryProcessed.api";

import DataTable from "../../components/ui/DataTable";
import ProcessFormModal from "./components/ProcessFormModal";
import ProcesoDetailModal from "./components/ProcessModal";

import { useAuth } from "../auth/AuthContext";


// import type { Inventory } from "../inventory/models/types";

import type { Parchment } from "./mapper/parchment.mapper";
import type { Product } from "../products/models/types";



type setActiveMenuItem = (item: number) => void;

interface SidebarProps {
  setActiveMenuItem: setActiveMenuItem;
}

/**
 * Page for managing the processed (roasted) coffee inventory.
 *
 * Allows:
 * - Listing all processes
 * - Searching processes
 * - Creating new processes with detail lines
 * - Viewing the detail of a process in a read-only modal
 */
export default function InventoryProcessedPage({
  setActiveMenuItem,
}: SidebarProps) {
  const [data, setData] = useState<Process[]>([]);
  const [search, setSearch] = useState("");

  // ── Create modal ────────────────────────────────────────────────────────────
  const [addingProceso, setAddingProceso] = useState(false);

  // ── Detail view modal ───────────────────────────────────────────────────────
  const [viewingProceso, setViewingProceso] = useState<Process | null>(null);
  const [detalles, setDetalles] = useState<ProcessDetail[]>([]);
  const [loadingDetalles, setLoadingDetalles] = useState(false);

  const { user } = useAuth();





  const [parchments, setParchments] = useState<Parchment[]>([]);

  useEffect(() => {
    fetchParchments().then(setParchments);
  }, []);
  
  
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    fetchProducts().then(setProducts);
  }, []);

  // ── Data loading ────────────────────────────────────────────────────────────

  const loadProcesos = async (): Promise<void> => {
    const procesos = await fetchProcesos({ search });
    setData(procesos);
  };

  useEffect(() => {
    loadProcesos();
  }, [search]);

  // ── Open detail modal ────────────────────────────────────────────────────────

  const handleView = async (proceso: Process) => {
    setViewingProceso(proceso);
    setDetalles([]);
    setLoadingDetalles(true);
    try {
      const result = await fetchDetallesByProceso(proceso.id);
      setDetalles(result);
    } finally {
      setLoadingDetalles(false);
    }
  };

  // ── Create ───────────────────────────────────────────────────────────────────

  const handleCreate = async (payload: CreateProcessPayload): Promise<void> => {
    await runWithAlert(async () => {
      await createProceso(payload);
      await loadProcesos();
      setAddingProceso(false);
    }, "Proceso creado correctamente");
  };

  // ── Columns with custom "Ver" action ─────────────────────────────────────────
  //
  // We inject a custom render for the `edit` column so the table shows
  // both the standard Edit button (managed by DataTable) and a "Ver" button.
  // If your DataTable doesn't support injecting extra cells this way,
  // you can pass an `extraActions` prop or render the column here directly.
  //
  // The column definition below replaces the `edit` column's cell renderer
  // so DataTable doesn't need modifications.

  const columnsWithView = ProcessColumns.map((col) => {
    if ((col as any).accessorKey === "edit") {
      return {
        ...col,
        cell: ({ row }: any) => (
          <div className="flex items-center gap-2">
            {/* Ver */}
            <button
              onClick={() => handleView(row.original)}
              className="flex items-center gap-1.5 text-xs bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 px-3 py-1.5 rounded-lg font-medium transition-all duration-200 hover:scale-105"
            >
              <Eye className="w-3.5 h-3.5" />
              Ver
            </button>
          </div>
        ),
      };
    }
    return col;
  });

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-6">
      {/* Page title */}
      <div className="flex flex-col gap-6">
        <div className="text-3xl font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex justify-center items-center hover:cursor-pointer hover:scale-105 transition-transform duration-400">
              <CirclePlus
                onClick={() => setAddingProceso(true)}
                className="inline w-8 h-8 text-emerald-900 font-bold"
              />
            </div>
            Gestión de inventario café procesado
          </div>

          <button
            className="text-xl bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200 flex items-center gap-2"
            onClick={() => setActiveMenuItem(6)}
          >
            <Replace className="w-5 h-5" />
            Inventario pergamino
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="flex text-sm font-semibold text-gray-700 mb-2">
              Buscar proceso
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar por factura, caficultor…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="text-sm w-full border border-gray-200 rounded-xl px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-emerald-900 focus:border-transparent transition-all duration-200 hover:border-emerald-900"
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            </div>
          </div>

          <div className="flex gap-2 flex-col md:flex-row w-max">
            <button
              onClick={() => setSearch("")}
              className="text-sm h-11 bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 flex items-center gap-2 border border-gray-200"
            >
              <X className="w-5 h-5" />
              Limpiar
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columnsWithView}
        data={data}
        onEdit={() => {}} // edit not used for processes (view-only detail)
        isAdmin={user?.role === "admin"}
      />

      {/* Create modal */}
      {addingProceso && (
        <ProcessFormModal
          onClose={() => setAddingProceso(false)}
          onSave={handleCreate}
          parchments={parchments}
          products={products}
        />
      )}

      {/* Detail view modal */}
      {viewingProceso && (
        <ProcesoDetailModal
          proceso={viewingProceso}
          detalles={detalles}
          loading={loadingDetalles}
          onClose={() => {
            setViewingProceso(null);
            setDetalles([]);
          }}
        />
      )}
    </div>
  );
}
