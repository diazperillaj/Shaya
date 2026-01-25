import { useState } from "react"
import type { FormEvent } from "react"
import { User, Lock, Eye, EyeOff } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { login } from "./service"
import { useAuth } from "./AuthContext"

/**
 * Página de autenticación.
 *
 * Renderiza el formulario de inicio de sesión y gestiona
 * el flujo completo de autenticación:
 * - Captura de credenciales
 * - Llamada al servicio de login
 * - Refresco del usuario autenticado
 * - Redirección a la aplicación principal
 */
export default function AuthPage() {

  /**
   * Nombre de usuario ingresado por el usuario.
   */
  const [username, setUsername] = useState('')

  /**
   * Contraseña ingresada por el usuario.
   */
  const [password, setPassword] = useState('')

  /**
   * Controla la visibilidad de la contraseña.
   */
  const [showPassword, setShowPassword] = useState(false)

  /** Hook de navegación */
  const navigate = useNavigate()

  /** Función para refrescar el usuario autenticado */
  const { refreshUser } = useAuth()

  /**
   * Maneja el envío del formulario de login.
   *
   * Ejecuta la autenticación, actualiza el contexto
   * de usuario y redirige al inicio si es exitoso.
   *
   * @param e Evento de envío del formulario
   */
  const handleSubmit = async (
    e: FormEvent<HTMLFormElement>
  ): Promise<void> => {
    e.preventDefault()

    try {
      await login({ username, password })
      await refreshUser()
      navigate('/')
    } catch (err: any) {
      alert(err.message)
    }
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md animate-slideUp">

        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-900 via-emerald-800 to-emerald-900 rounded-t-2xl px-6 py-6 flex items-center justify-center">
          <h1 className="text-2xl font-semibold text-white flex items-center gap-3">
            Shaya Café
          </h1>
        </div>

        {/* Body */}
        <form
          onSubmit={handleSubmit}
          className="p-6 flex flex-col gap-5"
        >
          {/* Usuario */}
          <div className="flex flex-col gap-2">
            <label className="text-md font-semibold text-gray-700 ps-2">
              Usuario
            </label>
            <div className="relative">
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Ingrese su usuario"
                required
                minLength={4}
                className="text-sm border border-gray-200 rounded-xl px-4 py-3 pl-11 focus:outline-1 outline-emerald-700 transition-colors duration-400 w-full"
              />
              <User className="w-5 h-5 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
            </div>
          </div>

          {/* Contraseña */}
          <div className="flex flex-col gap-2">
            <label className="text-md font-semibold text-gray-700 ps-2">
              Contraseña
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Ingrese su contraseña"
                required
                minLength={6}
                className="text-sm border border-gray-200 rounded-xl px-4 py-3 pl-11 pr-12 focus:outline-1 outline-emerald-700 duration-400 w-full"
              />
              <Lock className="w-5 h-5 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
              <button
                type="button"
                onClick={() => setShowPassword(prev => !prev)}
                className="absolute right-4 top-1/2 -translate-y-1/2"
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5 text-gray-400" />
                ) : (
                  <Eye className="w-5 h-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          {/* Botón */}
          <button
            type="submit"
            className="m-auto w-1/2 mt-4 bg-emerald-900 hover:bg-emerald-950 text-white py-3 rounded-xl font-medium shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-200"
          >
            Iniciar sesión
          </button>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-2xl border-t border-gray-100 text-center text-sm text-gray-500">
          © {new Date().getFullYear()} Shaya Café
        </div>
      </div>
    </div>
  )
}
