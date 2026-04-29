// ─── Field Types ────────────────────────────────────────────────────────────

export interface ProcessSelectOption {
  value: string | number;
  label: string;
  /** Extra data attached to option — e.g. kg for pergamino seco */
  metadata?: { kg?: number; [key: string]: unknown };
}

export type ProcessFieldType = "text" | "number" | "date" | "select" | "textarea";

export interface ProcessField {
  accessor: string;
  header: string;
  type: ProcessFieldType;
  options?: ProcessSelectOption[];
  required?: boolean;
}

export interface DetalleField {
  accessor: string;
  header: string;
  type: ProcessFieldType;
  options?: ProcessSelectOption[];
  required?: boolean;
}

// ─── Data Types ──────────────────────────────────────────────────────────────

/** One line of the detalle proceso (auto-fields: IVA, Total) */
export interface DetalleItem {
  _tempId: string; // internal — not sent to backend
  Producto_Nombre: string;
  Cantidad_Bolsas: number;
  /** Grams per bag */
  Cantidad_g: number;
  Valor_Unitario: number;
  /** Auto: Valor_Unitario × 0.05 */
  IVA: number;
  /** Auto: (Cantidad_Bolsas × Valor_Unitario) + IVA */
  Total: number;
  Observaciones: string;
}

/** Detalle sent to backend (no internal _tempId) */
export type DetallePayload = Omit<DetalleItem, "_tempId">;

/** Generic map for the main process form data */
export type ProcesoFormData = Record<string, unknown>;

/** Full process payload sent to backend (form + auto-calculated fields) */
export interface ProcesoPayload extends ProcesoFormData {
  /** Sum of (Bolsas × g) / 1000 across all detalles */
  Resultante: number;
  /** (Resultante / Pergamino_Kg) × 100 */
  Rendimiento: number;
  /** Sum of (Bolsas × Valor_Unitario) across all detalles */
  Subtotal: number;
  /** Sum of (Valor_Unitario × 0.05) across all detalles */
  IVA: number;
  /** Sum of Total across all detalles */
  Total: number;
}