import type { TableField } from "../../../models/common";
import type { Inventory } from "./types";

/**
 * Definición de los campos del formulario de inventario.
 *
 * Describe de forma declarativa cómo deben renderizarse
 * los campos asociados a la entidad `Inventory`.
 */

export const InventoryFields: TableField<Inventory>[] = [
  {
    accessor: "farmer",
    header: "Caficultor",
    type: "select",
    options: [],
  },

  { accessor: "variety", header: "Variedad", type: "text" },

  { accessor: "elevation", header: "Altitud (m.s.n.m)", type: "number" },

  { accessor: "humidity", header: "Humedad (%)", type: "number" },
  
  { accessor: "full_price", header: "Precio por carga", type: "number" },

  { accessor: "quantity", header: "Cantidad inicial (Kg)", type: "number" },

  { accessor: "date", header: "Fecha de compra", type: "date" },

  { accessor: "observation", header: "Observaciones", type: "textarea" },
  
];


export const InventoryEditFields: TableField<Inventory>[] = InventoryFields.map(field => {
  if (field.accessor === "quantity") {
    return {
      ...field,
      accessor: "remaining_quantity",
      header: "Cantidad restante (Kg)"
    };
  }
  return field;
});