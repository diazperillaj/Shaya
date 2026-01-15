// src/models/common.ts
export interface TableField<T> {
  accessor: keyof T;
  header: string;
}

export interface TableColumn<T> extends TableField<T> {
  id?: string; // para la columna de acciones
}
