import type { TableField } from "../../../models/common";
import type { Inventory } from "./types";

/**
 * Definición de los campos del formulario de inventario.
 *
 * Describe de forma declarativa cómo deben renderizarse
 * los campos asociados a la entidad `Inventory`.
 */

export const InventoryFields: TableField<Inventory>[] = [
  /** Caficultor */
  {
    accessor: "farmer",
    header: "Caficultor",
    type: "select",
    options: []
  },

  /** Variedad del café */
  { accessor: "variety", header: "Variedad", type: "text" },

  /** Altitud del lote */
  { accessor: "elevation", header: "Altitud (m.s.n.m)", type: "number" },

  /** Humedad del lote */
  { accessor: "humidity", header: "Humedad (%)", type: "number" },

  /** Rendimiento del lote */
  { accessor: "yield_factor", header: "Factor de rendimiento", type: "number" },

  /** Precio de compra */
  { accessor: "price", header: "Precio de compra", type: "number" },
  
  /** Precio por carga */
  { accessor: "full_price", header: "Precio por carga", type: "number" },

  /** Cantidad inicial del lote */
  { accessor: "quantity", header: "Cantidad inicial (Kg)", type: "number" },

  /** Fecha de compra */
  { accessor: "date", header: "Fecha de compra", type: "date" },

  /** Observaciones */
  { accessor: "observation", header: "Observaciones", type: "textarea" },
];
