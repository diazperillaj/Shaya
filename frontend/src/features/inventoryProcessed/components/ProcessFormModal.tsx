// features/inventoryProcessed/components/ProcessFormModal.tsx
//
// Modal for CREATING a new process (with detail lines).
// Edit mode only updates the header fields; details are read-only
// (shown via the separate ProcesoDetailModal).

import { useState } from "react";
import { X, FlaskConical, Plus, Trash2, Save, PackagePlus } from "lucide-react";
import type {
  CreateProcessPayload,
  CreateProcessDetailPayload,
} from "../models/types";
// import type { Inventory } from "../../inventory/models/types";
import type { Parchment } from "../mapper/parchment.mapper";
import type { Product } from "../../products/models/types";

// ─── Types ────────────────────────────────────────────────────────────────────

interface ProcessFormModalProps {
  onClose: () => void;
  onSave: (payload: CreateProcessPayload) => Promise<void>;
  parchments: Parchment[];
  products: Product[];
}

interface DetailRow extends CreateProcessDetailPayload {
  /** local-only key so React can track rows before they have a DB id */
  _key: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

let _keyCounter = 0;
const nextKey = () => ++_keyCounter;

const emptyDetail = (): DetailRow => ({
  _key: nextKey(),
  product_id: null,
  bag_quantity: 0,
  grams_per_bag: 0,
  unit_value: 0,
  observations: "",
});

const fmtCOP = (n: number): string =>
  n.toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  });

// ─── Component ───────────────────────────────────────────────────────────────

export default function ProcessFormModal({
  onClose,
  onSave,
  parchments,
  products,
}: ProcessFormModalProps) {
  // ── Header state ────────────────────────────────────────────────────────────
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [processDate, setProcessDate] = useState("");
  const [parchment_id, setParchmentId] = useState("");
  const [parchmentKg, setParchmentKg] = useState<number>(0);
  const [observations, setObservations] = useState("");

  // ── Detail lines ────────────────────────────────────────────────────────────
  const [details, setDetails] = useState<DetailRow[]>([emptyDetail()]);

  // ── Derived financials ──────────────────────────────────────────────────────
  const resultante = details.reduce(
    (acc, d) => acc + (d.bag_quantity * d.grams_per_bag) / 1000,
    0,
  );
  const rendimiento = parchmentKg > 0 ? (resultante / parchmentKg) * 100 : 0;
  const subtotal = details.reduce(
    (acc, d) => acc + d.unit_value * d.bag_quantity,
    0,
  );
  const iva = subtotal * 0.052;
  const total = subtotal + iva;

  // ── Saving ──────────────────────────────────────────────────────────────────
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    // Basic validation
    if (!invoiceNumber.trim())
      return setError("El número de factura es requerido.");
    if (!processDate) return setError("La fecha es requerida.");
    if (!parchment_id.trim())
      return setError("El nombre del caficultor es requerido.");
    if (parchmentKg <= 0)
      return setError("El pergamino (Kg) debe ser mayor a 0.");
    if (details.some((d) => d.product_id === null))
      return setError("Todos los detalles deben tener un producto seleccionado.");
    if (details.some((d) => d.bag_quantity <= 0 || d.grams_per_bag <= 0))
      return setError("Cantidad de bolsas y gramos deben ser mayores a 0.");

    setError(null);
    setSaving(true);
    try {
      const payload: CreateProcessPayload = {
        invoice_number: invoiceNumber.trim(),
        process_date: processDate,
        parchment_id: parseInt(parchment_id),
        parchment_kg: parchmentKg,
        observations: observations.trim() || undefined,
        details: details.map(({ _key, ...d }) => d),
      };
      await onSave(payload);
    } catch (err: any) {
      setError(err.message || "Error al guardar el proceso.");
    } finally {
      setSaving(false);
    }
  };

  // ── Detail helpers ──────────────────────────────────────────────────────────
  const addDetail = () => setDetails((prev) => [...prev, emptyDetail()]);

  const removeDetail = (key: number) =>
    setDetails((prev) => prev.filter((d) => d._key !== key));

  const updateDetail = <K extends keyof DetailRow>(
    key: number,
    field: K,
    value: DetailRow[K],
  ) =>
    setDetails((prev) =>
      prev.map((d) => (d._key === key ? { ...d, [field]: value } : d)),
    );

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[95vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-5 flex items-center justify-between flex-shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center gap-3">
            <FlaskConical className="w-5 h-5 flex-shrink-0" />
            Nuevo proceso de café tostado
          </h2>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white hover:bg-white/10 rounded-lg p-2 transition-all duration-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 p-6 space-y-7 scrollbar-thin scrollbar-thumb-emerald-200 scrollbar-track-gray-100">
          {/* ── Section 1: Process header ─────────────────────────────────── */}
          <section>
            <SectionTitle label="Datos del proceso" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <FormField label="No. Factura" required>
                <input
                  type="text"
                  value={invoiceNumber}
                  onChange={(e) => setInvoiceNumber(e.target.value)}
                  placeholder="Ej: FAC-0001"
                  className={inputCls}
                />
              </FormField>

              <FormField label="Fecha" required>
                <input
                  type="date"
                  value={processDate}
                  onChange={(e) => setProcessDate(e.target.value)}
                  className={inputCls}
                />
              </FormField>

              <FormField label="Pergamino" required>
                <select
                  value={parchment_id}
                  onChange={(e) => setParchmentId(e.target.value)}
                  className={inputCls}
                >
                  <option value="" disabled>
                    Lote pergamino usado
                  </option>

                  {parchments.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.id} - {p.farmer.person.full_name} - {p.variety} -{" "}
                      {p.remaining_quantity} Kg
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField label="Pergamino enviado (Kg)" required>
                <input
                  type="number"
                  min={0}
                  step={0.01}
                  value={parchmentKg || ""}
                  onChange={(e) => setParchmentKg(Number(e.target.value))}
                  placeholder="0.00"
                  className={inputCls}
                />
              </FormField>

              {/* Read-only derived fields */}
              <FormField label="Resultante (Kg)">
                <div className={readonlyCls}>{resultante.toFixed(2)} Kg</div>
              </FormField>

              <FormField label="Rendimiento (%)">
                <div className={readonlyCls}>{rendimiento.toFixed(1)} %</div>
              </FormField>
            </div>

            <div className="mt-4">
              <FormField label="Observaciones">
                <textarea
                  value={observations}
                  onChange={(e) => setObservations(e.target.value)}
                  rows={2}
                  placeholder="Observaciones del proceso (opcional)"
                  className={`${inputCls} resize-none`}
                />
              </FormField>
            </div>
          </section>

          {/* ── Section 2: Financial summary ──────────────────────────────── */}
          <section>
            <SectionTitle label="Resumen financiero (calculado)" />
            <div className="grid grid-cols-3 gap-3">
              <FinanceCard label="Subtotal" value={fmtCOP(subtotal)} />
              <FinanceCard label="IVA (5.2%)" value={fmtCOP(iva)} />
              <FinanceCard label="Total" value={fmtCOP(total)} highlight />
            </div>
          </section>

          {/* ── Section 3: Detail lines ───────────────────────────────────── */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <PackagePlus className="w-4 h-4 text-emerald-700" />
                <span className="text-sm font-semibold text-emerald-800 uppercase tracking-wider">
                  Detalle del proceso
                </span>
                <span className="bg-emerald-800 text-white text-xs font-bold rounded-full px-2 py-0.5">
                  {details.length}
                </span>
              </div>
            </div>

            <div className="space-y-3">
              {details.map((det, idx) => (
                <DetailLine
                  key={det._key}
                  index={idx}
                  detail={det}
                  onChange={(field, value) =>
                    updateDetail(det._key, field, value)
                  }
                  onRemove={() => removeDetail(det._key)}
                  canRemove={details.length > 1}
                  products={products}
                />
              ))}
            </div>
            <button
              onClick={addDetail}
              className="flex items-center m-5 gap-1.5 text-sm bg-emerald-900 hover:bg-emerald-950 text-white px-4 py-2 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200"
            >
              <Plus className="w-4 h-4" />
              Agregar línea
            </button>
          </section>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 flex-shrink-0 flex justify-between items-center gap-3">
          <button
            onClick={onClose}
            className="flex items-center gap-2 bg-white hover:bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium shadow-sm hover:shadow-md transform hover:scale-105 transition-all duration-200 border border-gray-200"
          >
            <X className="w-4 h-4" />
            Cancelar
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-emerald-900 hover:bg-emerald-950 disabled:opacity-60 text-white px-6 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
          >
            {saving ? (
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Guardar proceso
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── DetailLine ───────────────────────────────────────────────────────────────

interface DetailLineProps {
  index: number;
  detail: DetailRow;
  onChange: <K extends keyof DetailRow>(field: K, value: DetailRow[K]) => void;
  onRemove: () => void;
  canRemove: boolean;
  products: Product[];
}

function DetailLine({
  index,
  detail,
  onChange,
  onRemove,
  canRemove,
  products,
}: DetailLineProps) {
  const lineSubtotal = detail.unit_value * detail.bag_quantity;
  const lineIva = lineSubtotal * 0.052;
  const lineTotal = lineSubtotal + lineIva;
  const lineKg = (detail.bag_quantity * detail.grams_per_bag) / 1000;
  const [productId, setProductId] = useState<number>(0);
  const [rendimiento, setRendimiento] = useState(0);

  return (
    <div className="bg-gray-50 border border-gray-100 rounded-2xl p-4 space-y-3">
      {/* Row header */}
      <div className="flex items-center justify-between">
        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
          {index + 1}
        </span>
        {canRemove && (
          <button
            onClick={onRemove}
            className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg px-2 py-1 transition-all duration-200"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Eliminar
          </button>
        )}
      </div>

      {/* Fields grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="col-span-2 sm:col-span-1 lg:col-span-1">
          <FormField label="Producto" required>
            <select
              value={productId}
              onChange={(e) => {
                const productId = Number(e.target.value);

                setProductId(productId);


                const product = products.find((p) => p.id === productId);
                if (product) {
                  
                  onChange("product_id", product.id);
                  onChange("grams_per_bag", product.quantity);
                  setRendimiento(product.quantity * detail.bag_quantity);
                }
              }}
              className={inputCls}
            >
              <option value="" disabled>
                Producto
              </option>

              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.id} - {p.name}
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField label="Bolsas">
          <input
            type="number"
            min={0}
            value={detail.bag_quantity || ""}
            onChange={(e) => {
              onChange("bag_quantity", Number(e.target.value));

                const product = products.find((p) => p.id === productId);
                if (product) {
                  onChange("grams_per_bag", product.quantity);
                  setRendimiento(product.quantity * Number(e.target.value));
                }
            }}
            placeholder="0"
            className={inputCls}
          />
        </FormField>

        <FormField label="Gramos / bolsa">
          <div className={readonlyCls}>{rendimiento}</div>
        </FormField>

        <FormField label="Valor unitario">
          <input
            type="number"
            min={0}
            value={detail.unit_value || ""}
            onChange={(e) => onChange("unit_value", Number(e.target.value))}
            placeholder="0"
            className={inputCls}
          />
        </FormField>

        <div className="col-span-2 sm:col-span-3 lg:col-span-4">
          <FormField label="Observaciones">
            <input
              type="text"
              value={detail.observations || ""}
              onChange={(e) => onChange("observations", e.target.value)}
              placeholder="Observaciones (opcional)"
              className={inputCls}
            />
          </FormField>
        </div>
      </div>

      {/* Line totals */}
      <div className="flex flex-wrap gap-3 pt-1">
        <Badge label="Kg resultante" value={`${lineKg.toFixed(3)} Kg`} />
        <Badge label="Subtotal" value={fmtCOP(lineSubtotal)} />
        <Badge label="IVA" value={fmtCOP(lineIva)} />
        <Badge label="Total línea" value={fmtCOP(lineTotal)} accent />
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function SectionTitle({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="h-px flex-1 bg-emerald-100" />
      <span className="text-xs font-semibold text-emerald-700 uppercase tracking-widest whitespace-nowrap">
        {label}
      </span>
      <div className="h-px flex-1 bg-emerald-100" />
    </div>
  );
}

function FormField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

function FinanceCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`flex flex-col items-center gap-1 rounded-xl py-4 px-3 border ${
        highlight
          ? "bg-emerald-900 border-emerald-800 text-white"
          : "bg-emerald-50 border-emerald-100"
      }`}
    >
      <span
        className={`text-xs font-medium uppercase tracking-wide ${
          highlight ? "text-emerald-200" : "text-emerald-600"
        }`}
      >
        {label}
      </span>
      <span
        className={`text-base font-bold ${highlight ? "text-white" : "text-emerald-900"}`}
      >
        {value}
      </span>
    </div>
  );
}

function Badge({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs border ${
        accent
          ? "bg-emerald-100 border-emerald-200 text-emerald-800 font-bold"
          : "bg-white border-gray-200 text-gray-600"
      }`}
    >
      <span className="font-medium">{label}:</span>
      <span>{value}</span>
    </div>
  );
}

// ─── Shared styles ────────────────────────────────────────────────────────────

const inputCls =
  "w-full text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-900 focus:border-transparent transition-all duration-200 hover:border-emerald-900 bg-white";

const readonlyCls =
  "w-full text-sm border border-gray-100 rounded-xl px-3 py-2.5 bg-gray-50 text-gray-500 font-medium";
