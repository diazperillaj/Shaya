/**
 * Roles de usuario del sistema (mismos valores que el backend).
 *
 * - `admin` y `user`: personal de Shaya, con acceso a los módulos del negocio.
 * - `farmer`: caficultor externo; solo accede al módulo de cultivo.
 */
export type Role = 'admin' | 'user' | 'farmer'

/** Roles con acceso a los módulos del negocio */
export const STAFF_ROLES: readonly Role[] = ['admin', 'user']

/** Roles con acceso al módulo de cultivo */
export const FARM_ROLES: readonly Role[] = ['admin', 'farmer']

/**
 * Indica si un rol está entre los permitidos.
 */
export const hasRole = (
  role: string | undefined,
  allowed: readonly Role[]
): boolean => allowed.includes(role as Role)

/**
 * Pantalla de inicio de cada rol: el personal entra al sistema del negocio
 * y el caficultor directamente a Cultivo.
 *
 * @returns La ruta de inicio, o null si el rol no tiene acceso a ninguna
 */
export const homePathFor = (role: string | undefined): string | null => {
  if (hasRole(role, STAFF_ROLES)) return '/'
  if (hasRole(role, FARM_ROLES)) return '/cultivo'
  return null
}
