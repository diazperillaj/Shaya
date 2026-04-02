import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { ReactNode } from 'react'

/**
 * Props del componente ProtectedRoute.
 */
interface ProtectedRouteProps {
  /** Componentes hijos que requieren autenticación */
  children: ReactNode
}

/**
 * Componente de ruta protegida.
 *
 * Restringe el acceso a rutas que requieren
 * un usuario autenticado.
 *
 * Flujo de funcionamiento:
 * - Mientras el estado de autenticación se carga, no renderiza nada
 * - Si no hay usuario autenticado, redirige a /login
 * - Si el usuario está autenticado, renderiza los hijos
 */
export default function ProtectedRoute({
  children,
}: ProtectedRouteProps) {
  const { user, loading } = useAuth()

  // Mientras se valida la sesión
  if (loading) return null

  // Usuario no autenticado
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Usuario autenticado
  return children
}
