import type { CustomerApiResponse } from '../models/types'

/**
 * Mapea un cliente proveniente de la API
 * al modelo utilizado en el frontend.
 *
 * Este mapper desacopla la estructura del backend
 * (datos personales anidados en `person`)
 * del modelo plano consumido por la interfaz.
 *
 * @param u Cliente recibido desde la API
 * @returns Cliente adaptado al modelo del frontend
 */
export const mapCustomerFromApi = (u: CustomerApiResponse) => ({
  /** Identificador único del caficultor */
  id: u.id,

  /** Nombre completo de la persona */
  name: u.person.full_name,

  /** Documento de identificación */
  document: u.person.document,

  /** Correo electrónico */
  email: u.person.email,

  /** Tipo de cliente */
  customerType: u.customerType,

  /** Direccion del cliente */
  address: u.address,

  /** Ciudad del cliente */
  city: u.city,

  /** Teléfono de contacto */
  phone: u.person.phone,

  /**
   * Observaciones del cliente.
   * Se asigna un valor por defecto si la API no lo envía.
   */
  observation: u.person.observation || 'Sin observación',
})
