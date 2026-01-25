import { createContext, useContext, useEffect, useState } from 'react'
import type { User } from './schema'
import { getMe } from './service'

/**
 * Contrato del contexto de autenticación.
 *
 * Define la información y acciones disponibles
 * para cualquier componente que consuma el contexto.
 */
interface AuthContextType {

  /** Usuario autenticado actualmente (null si no hay sesión) */
  user: User | null

  /** Indica si el estado de autenticación está cargando */
  loading: boolean

  /**
   * Fuerza la recarga de la información del usuario
   * desde el backend.
   */
  refreshUser: () => Promise<void>
}

/**
 * Contexto de autenticación.
 *
 * Se inicializa como null y se valida en el hook `useAuth`
 * para asegurar su uso correcto.
 */
const AuthContext = createContext<AuthContextType | null>(null)

/**
 * Proveedor de autenticación.
 *
 * Envuelve la aplicación y mantiene el estado global
 * del usuario autenticado.
 *
 * Responsabilidades:
 * - Obtener el usuario autenticado al iniciar la app
 * - Exponer el usuario y estado de carga
 * - Permitir refrescar la sesión manualmente
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {

  /**
   * Usuario autenticado.
   */
  const [user, setUser] = useState<User | null>(null)

  /**
   * Indica si el estado de autenticación
   * está siendo cargado.
   */
  const [loading, setLoading] = useState(true)

  /**
   * Obtiene la información del usuario autenticado
   * desde la API.
   *
   * Si la sesión no es válida, el usuario se establece
   * como null.
   */
  const refreshUser = async (): Promise<void> => {
    try {
      const me = await getMe()
      setUser(me)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Carga inicial del usuario al montar
   * el proveedor.
   */
  useEffect(() => {
    refreshUser()
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook para consumir el contexto de autenticación.
 *
 * Garantiza que el hook sea utilizado únicamente
 * dentro de un `AuthProvider`.
 *
 * @throws Error si se usa fuera del AuthProvider
 */
export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)

  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return ctx
}
