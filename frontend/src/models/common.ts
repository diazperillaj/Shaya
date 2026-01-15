// src/models/common.ts

export type FieldType = 'text' | 'select' | 'password' | 'textarea';

export interface TableField<T> {
  accessor: keyof T;
  header: string;
}

export interface SelectOption {
  label: string;
  value: string | number;
}

export interface TableField<T> {
  accessor: keyof T;
  header: string;
  type?: FieldType;        // 👈 nuevo
  options?: SelectOption[]; // 👈 solo para select
}