import type { LoginPayload, User } from './schema'

/**
 * URL base del módulo de autenticación.
 */
const API_URL = 'http://localhost:8000/api/v1/auth'

/* =======================
   LOGIN
======================= */

/**
 * Inicia sesión en el sistema.
 *
 * Envía las credenciales al backend y establece
 * la sesión mediante cookies HTTP.
 *
 * @param payload Credenciales de inicio de sesión
 * @throws Error si las credenciales son inválidas
 */
export async function login(
  payload: LoginPayload
): Promise<void> {
  const res = await fetch(`${API_URL}/login`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const data = await res.json()
    throw new Error(data.detail || 'Error al iniciar sesión')
  }
}

/* =======================
   ME
======================= */

/**
 * Obtiene la información del usuario autenticado.
 *
 * Se utiliza para validar la sesión activa
 * y recuperar los datos básicos del usuario.
 *
 * @returns Usuario autenticado
 * @throws Error si no existe una sesión válida
 */
export async function getMe(): Promise<User> {
  const res = await fetch(`${API_URL}/me`, {
    credentials: 'include',
  })

  if (!res.ok) {
    throw new Error('No autenticado')
  }

  return res.json()
}

/* =======================
   LOGOUT
======================= */

/**
 * Cierra la sesión del usuario actual.
 *
 * Invalida la sesión en el backend y
 * elimina las cookies asociadas.
 */
export async function logout(): Promise<void> {
  await fetch(`${API_URL}/logout`, {
    method: 'POST',
    credentials: 'include',
  })
}
