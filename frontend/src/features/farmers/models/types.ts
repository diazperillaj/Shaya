// src/features/farmers/types.ts

/**
 * Representa un caficultor en el frontend.
 *
 * Este modelo se utiliza para:
 * - Mostrar información en tablas y formularios
 * - Enviar datos a la API al crear o actualizar caficultores
 *
 * Es un modelo plano, desacoplado de la estructura del backend.
 */
export interface Farmer {

  /** Identificador único del caficultor */
  id: number

  /** Nombre completo del caficultor */
  name: string

  /** Documento de identificación */
  document: string

  /** Correo electrónico */
  email: string

  /** Nombre de la finca */
  farm_name: string

  /** Ubicación de la finca */
  farm_location: string

  /** Teléfono de contacto */
  phone: string

  /** Observaciones adicionales */
  observation?: string
}

/**
 * Filtros disponibles para la consulta de caficultores.
 *
 * Se utilizan al solicitar la lista de caficultores
 * desde la API.
 */
export interface FarmersQuery {

  /** Texto de búsqueda (nombre, documento, finca, etc.) */
  search?: string
}

/**
 * Representa la estructura del caficultor
 * tal como la envía la API.
 *
 * Este tipo refleja fielmente el contrato del backend
 * y debe usarse únicamente en servicios y mappers.
 */
export interface FarmerApiResponse {

  /** Identificador único */
  id: number

  /** Nombre de la finca */
  farm_name: string

  /** Ubicación de la finca */
  farm_location: string

  /** Información personal asociada al caficultor */
  person: {
    full_name: string
    document: string
    email: string
    phone: string
    observation?: string | null
  }
}
