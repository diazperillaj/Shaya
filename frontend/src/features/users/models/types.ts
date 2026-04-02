// src/features/users/types.ts


/**
 * Representa un usuario del sistema en el frontend.
 *
 * Este modelo se utiliza para:
 * - Mostrar información en la interfaz
 * - Enviar datos a la API al crear o actualizar usuarios
 *
 * Algunos campos pueden no estar presentes dependiendo
 * del contexto (por ejemplo, password).
 */
export interface User {
  /** Identificador único del usuario */
  id: number;

  /** Nombre completo de la persona asociada al usuario */
  name: string;

  /** Documento de identificación */
  document: string;

  /** Nombre de usuario para autenticación */
  username: string;

  /**
   * Contraseña del usuario.
   *
   * Solo se utiliza al crear o actualizar el usuario.
   * Nunca debe almacenarse ni mostrarse en la interfaz.
   */
  password?: string;

  /** Correo electrónico del usuario */
  email: string;

  /** Número de teléfono de contacto */
  phone: string;

  /** Rol asignado al usuario dentro del sistema */
  role: string;

  /** Observaciones adicionales del usuario */
  observation?: string
}

/**
 * Filtros disponibles para la consulta de usuarios.
 *
 * Se utilizan al solicitar la lista de usuarios
 * desde la API.
 */
export interface UsersQuery {

  /** Texto de búsqueda (nombre, usuario, correo, etc.) */
  search?: string

  /** Rol por el cual filtrar usuarios */
  role?: string
}

/**
 * Representa la estructura de usuario
 * tal como la envía la API.
 */
export interface UserApiResponse {
  id: number
  username: string
  role: string
  person: {
    full_name: string
    document: string
    email: string
    phone: string
    observation?: string | null
  }
}
