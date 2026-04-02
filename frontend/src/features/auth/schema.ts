/**
 * Payload utilizado para la autenticación de usuarios.
 *
 * Representa las credenciales necesarias
 * para iniciar sesión en el sistema.
 */
export interface LoginPayload {

  /** Nombre de usuario */
  username: string

  /** Contraseña en texto plano */
  password: string
}

/**
 * Representa al usuario autenticado.
 *
 * Este modelo contiene únicamente la información
 * mínima necesaria para la gestión de sesión
 * y control de permisos en el frontend.
 */
export interface User {

  /** Identificador único del usuario */
  id: number

  /** Nombre de usuario autenticado */
  username: string

  /** Rol asignado al usuario dentro del sistema */
  role: string
}
