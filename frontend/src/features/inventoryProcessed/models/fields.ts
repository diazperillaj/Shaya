import type { TableField } from "../../../models/common";
import type { Inventory } from "./types";

/**
 * Definición de los campos del formulario de inventario procesado.
 *
 * Describe de forma declarativa cómo deben renderizarse
 * los campos asociados a la entidad `Inventory`.
 */

export const InventoryFields: TableField<Inventory>[] = [

  /** Información del lote de pergamino */
  { accessor: "parchment_info", header: "Info lote", type: "text" },

  /** Tipo de producto */
  {
    accessor: "type",
    header: "Tipo",
    type: "select",
    options: [
      { label: "Café molido", value: "Ground Coffee" },
      { label: "Café en grano", value: "Coffee Beans" }
    ]
  },

  /** Cantidad */
  { accessor: "amount", header: "Cantidad", type: "number" },

  /** Variedad */
  { accessor: "variety", header: "Variedad", type: "text" },

  /** Nivel de tostión */
  {
    accessor: "roast_level",
    header: "Nivel de tostión",
    type: "select",
    options: [
      { label: "Tostión clara", value: "Light Roast" },
      { label: "Tostión media", value: "Medium Roast" },
      { label: "Tostión media-oscura", value: "Medium-Dark Roast" },
      { label: "Tostión oscura", value: "Dark Roast" }
    ]
  },

  /** Precio por unidad */
  { accessor: "unity_price", header: "Precio por unidad", type: "number" }

];