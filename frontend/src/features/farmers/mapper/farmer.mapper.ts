import type { FarmerApiResponse } from '../models/types'

/**
 * Mapea un caficultor proveniente de la API
 * al modelo utilizado en el frontend.
 *
 * Este mapper desacopla la estructura del backend
 * (datos personales anidados en `person`)
 * del modelo plano consumido por la interfaz.
 *
 * @param u Caficultor recibido desde la API
 * @returns Caficultor adaptado al modelo del frontend
 */
export const mapFarmerFromApi = (u: FarmerApiResponse) => ({
  /** Identificador único del caficultor */
  id: u.id,

  /** Nombre completo de la persona */
  name: u.person.full_name,

  /** Documento de identificación */
  document: u.person.document ?? "Sin documento",

  /** Correo electrónico */
  email: u.person.email ?? "Sin correo",

  /** Nombre de la finca */
  farm_name: u.farm_name,

  /** Ubicación de la finca */
  village: u.village,

  
  municipality: u.municipality,

  /** Teléfono de contacto */
  phone: u.person.phone,

  /**
   * Observaciones del caficultor.
   * Se asigna un valor por defecto si la API no lo envía.
   */
  observation: u.person.observation || 'Sin observación',
})
