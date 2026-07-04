// features/inventoryProcessed/InventoryProcessedPage.tsx

import { useEffect, useState } from "react";
import { CirclePlus, Search, Replace, Newspaper } from "lucide-react";


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
  deleteProceso,
  fetchDetallesByProceso,
  fetchProcesoById,
  fetchParchments,
  fetchProducts,
  updateProceso,
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
  const [editingProceso, setEditingProceso] = useState<Process | null>(null);
  const [editingDetalles, setEditingDetalles] = useState<ProcessDetail[]>([]);

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
    try {
      const procesos = await fetchProcesos({ search });
      setData(procesos);
    } catch {
      setData([]);
    }
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

  const handleEdit = async (proceso: Process): Promise<void> => {
    const full = await fetchProcesoById(proceso.id);
    setEditingProceso(full.process);
    setEditingDetalles(full.details);
  };

  const handleUpdate = async (payload: CreateProcessPayload): Promise<void> => {
    if (!editingProceso) return;
    await runWithAlert(async () => {
      await updateProceso(editingProceso.id, payload);
      await loadProcesos();
      setEditingProceso(null);
      setEditingDetalles([]);
    }, "Proceso actualizado correctamente");
  };

  const handleDelete = async (): Promise<void> => {
    if (!editingProceso) return;
    await runWithAlert(async () => {
      await deleteProceso(editingProceso.id);
      await loadProcesos();
      setEditingProceso(null);
      setEditingDetalles([]);
    }, "Proceso eliminado correctamente");
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-6">
      {/* Page title */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-100 rounded-xl">
            <Newspaper className="w-6 h-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Procesos</h1>
            <p className="text-sm text-gray-400">{data.length} proceso{data.length !== 1 ? 's' : ''} registrado{data.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="flex items-center gap-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 px-5 py-2.5 rounded-xl text-sm font-medium shadow-sm hover:shadow-md transition-all"
            onClick={() => setActiveMenuItem(7)}
          >
            <Replace className="w-4 h-4" />
            Inventario pergamino
          </button>
          {user?.role === 'admin' && (
            <button onClick={() => setAddingProceso(true)} className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 text-white px-5 py-2.5 rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all">
              <CirclePlus className="w-4 h-4" /> Nuevo proceso
            </button>
          )}
        </div>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar proceso…"
          className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700 bg-white"
        />
      </div>

      {/* Table */}
      <DataTable
        columns={ProcessColumns}
        data={data}
        onEdit={handleEdit}
        onView={handleView}
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

      {editingProceso && (
        <ProcessFormModal
          onClose={() => {
            setEditingProceso(null);
            setEditingDetalles([]);
          }}
          onSave={handleUpdate}
          onDelete={handleDelete}
          parchments={parchments}
          products={products}
          initialProcess={editingProceso}
          initialDetails={editingDetalles}
          isEdit
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
