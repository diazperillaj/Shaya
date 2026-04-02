import type { User } from '../models/types'
import type { UserApiResponse } from '../models/types'

/**
 * Mapea un objeto de usuario proveniente de la API
 * al modelo `User` utilizado en el frontend.
 *
 * Este mapper desacopla la estructura del backend
 * (entidades anidadas, nombres de campos)
 * del modelo utilizado por la interfaz.
 *
 * @param u Usuario recibido desde la API
 * @returns Usuario adaptado al modelo del frontend
 */
export const mapUserFromApi = (u: UserApiResponse): User => ({
  /** Identificador único */
  id: u.id,

  /** Nombre completo de la persona */
  name: u.person.full_name,

  /** Documento de identificación */
  document: u.person.document,

  /** Nombre de usuario */
  username: u.username,

  /** Correo electrónico */
  email: u.person.email,

  /** Teléfono de contacto */
  phone: u.person.phone,

  /** Rol del usuario */
  role: u.role,

  /**
   * Observaciones del usuario.
   * Se asigna un valor por defecto si la API no lo envía.
   */
  observation: u.person.observation || 'Sin observación',
})
