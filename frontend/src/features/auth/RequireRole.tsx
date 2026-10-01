import { Navigate, useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { logout } from './service'
import { hasRole, homePathFor, type Role } from './roles'

/**
 * Props del componente RequireRole.
 */
interface RequireRoleProps {
  /** Roles con acceso a la sección */
  roles: readonly Role[]

  /** Contenido de la sección */
  children: ReactNode
}

/**
 * Restringe una sección a ciertos roles.
 *
 * Se usa dentro de `ProtectedRoute`, que ya garantiza la sesión.
 *
 * - Si el rol tiene acceso, renderiza la sección.
 * - Si no, lleva al usuario a su pantalla de inicio (un caficultor que entra
 *   a `/` termina en `/cultivo`).
 * - Si el rol no tiene acceso a ninguna sección, muestra un aviso en lugar
 *   de redirigir, para no caer en un ciclo de redirecciones.
 */
export default function RequireRole({ roles, children }: RequireRoleProps) {
  const { user } = useAuth()

  if (hasRole(user?.role, roles)) return children

  const home = homePathFor(user?.role)
  return home ? <Navigate to={home} replace /> : <NoAccess />
}

/**
 * Aviso para una cuenta cuyo rol no tiene acceso a ninguna sección.
 */
function NoAccess() {
  const { refreshUser } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async (): Promise<void> => {
    await logout()
    await refreshUser()
    navigate('/login')
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50 p-6">
      <div className="max-w-sm rounded-2xl border border-gray-100 bg-white p-6 text-center shadow-lg">
        <h1 className="text-lg font-semibold text-gray-900">Cuenta sin acceso</h1>
        <p className="mt-2 text-sm text-gray-500">
          Tu cuenta no tiene acceso a ninguna sección del sistema. Contacta al
          administrador.
        </p>
        <button
          onClick={handleLogout}
          className="mt-5 rounded-xl bg-emerald-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}
