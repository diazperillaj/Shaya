// src/models/common.ts

/**
 * Tipos de campos soportados por los formularios dinámicos.
 *
 * Define cómo debe renderizarse cada campo
 * dentro de tablas y modales genéricos.
 */
export type FieldType =
  | 'text'
  | 'select'
  | 'password'
  | 'textarea'

/**
 * Opción disponible para campos de tipo select.
 */
export interface SelectOption {

  /** Texto visible para el usuario */
  label: string

  /** Valor real enviado o almacenado */
  value: string | number
}

/**
 * Definición genérica de un campo de tabla o formulario.
 *
 * Se utiliza para describir de forma declarativa
 * cómo renderizar y vincular campos de cualquier entidad.
 *
 * @template T Modelo al que pertenece el campo
 */
export interface TableField<T> {

  /**
   * Propiedad del modelo asociada al campo.
   * Debe existir en el tipo T.
   */
  accessor: keyof T

  /** Título visible del campo o columna */
  header: string

  /**
   * Tipo de campo a renderizar.
   * Si no se especifica, se asume un campo de texto.
   */
  type?: FieldType

  /**
   * Opciones disponibles para campos de tipo select.
   * Solo aplica cuando `type` es 'select'.
   */
  options?: SelectOption[]
}
