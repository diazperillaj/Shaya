// src/features/Customer/types.ts

/**
 * Representa un cliente en el frontend.
 *
 * Este modelo se utiliza para:
 * - Mostrar información en tablas y formularios
 * - Enviar datos a la API al crear o actualizar clientes
 *
 * Es un modelo plano, desacoplado de la estructura del backend.
 */
export interface Customer {

  /** Identificador único del cliente */
  id: number

  /** Nombre completo del cliente */
  name: string

  /** Documento de identificación */
  document: string

  /** Correo electrónico */
  email: string

  /** Tipo de cliente */
  customerType: string

  /** Direccion del cliente */
  address: string

  /** Ciudad del cliente */
  city: string

  /** Teléfono de contacto */
  phone: string

  /** Observaciones adicionales */
  observation?: string
}

/**
 * Filtros disponibles para la consulta de clientes.
 *
 * Se utilizan al solicitar la lista de clientes
 * desde la API.
 */
export interface CustomersQuery {

  /** Texto de búsqueda (nombre, documento, ciudad, etc.) */
  search?: string
}

/**
 * Representa la estructura del cliente
 * tal como la envía la API.
 *
 * Este tipo refleja fielmente el contrato del backend
 * y debe usarse únicamente en servicios y mappers.
 */
export interface CustomerApiResponse {

  /** Identificador único */
  id: number

  /** Tipo de cliente */
  customerType: string

  /** Direccion del cliente */
  address: string

  /** Ciudad del cliente */
  city: string

  /** Información personal asociada al cliente */
  person: {
    full_name: string
    document: string
    email: string
    phone: string
    observation?: string | null
  }
}
