import type { User, UsersQuery } from '../models/types'
import { mapUserFromApi } from '../mapper/user.mapper'

/**
 * URL base del módulo de usuarios.
 * Centraliza el endpoint para facilitar cambios de entorno.
 */
const BASE_URL = 'http://localhost:8000/api/v1/users'

/* =======================
   GET
======================= */


/**
 * Obtiene la lista de usuarios desde la API.
 *
 * Permite aplicar filtros opcionales como búsqueda por texto
 * y filtrado por rol.
 *
 * @param filters Filtros opcionales para la consulta de usuarios
 * @returns Lista de usuarios mapeados al modelo de frontend
 * @throws Error si la petición falla
 */
export const fetchUsers = async (filters?: UsersQuery): Promise<User[]> => {
  const query = new URLSearchParams()

  if (filters?.search) query.append('search', filters?.search)
  if (filters?.role) query.append('role', filters?.role)

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`,
    {
      credentials: 'include',
    })
  if (!res.ok) throw new Error('Error obteniendo usuarios')

  const data = await res.json()

  // Mapeamos la respuesta de la API al modelo del frontend
  return data.map(mapUserFromApi)
}

/* =======================
   CREATE
======================= */

/**
 * Crea un nuevo usuario en el sistema.
 *
 * Transforma el modelo de frontend al formato esperado por la API,
 * incluyendo la información personal anidada.
 *
 * @param user Usuario a crear
 * @returns Usuario creado y mapeado al modelo del frontend
 * @throws Error si la creación falla
 */
export const createUser = async (user: User): Promise<User> => {
  const payload = {
    username: user.username,
    password: user.password,
    role: user.role || 'user',
    person: {
      full_name: user.name,
      document: user.document,
      email: user.email,
      phone: user.phone,
      observation: user.observation,
    },
  }

  console.log(payload)

  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  console.log(data.detail)

  if (!res.ok) {
    throw new Error(data.detail || 'Error creando usuario')
  }

  if (!res.ok) throw new Error('Error creando usuario')

  return mapUserFromApi(data)
}

/* =======================
   UPDATE
======================= */

/**
 * Actualiza un usuario existente.
 *
 * La contraseña solo se envía si fue modificada,
 * evitando sobrescrituras innecesarias.
 *
 * @param user Usuario con la información actualizada
 * @returns Usuario actualizado y mapeado al modelo del frontend
 * @throws Error si la actualización falla
 */
export const updateUser = async (user: User): Promise<User> => {
  const payload: any = {
    username: user.username,
    role: user.role || 'user',
    person: {
      full_name: user.name,
      document: user.document,
      email: user.email,
      phone: user.phone,
      observation: user.observation,
    },
  }

  // Solo enviamos password si fue modificado
  if (user.password) {
    payload.password = user.password
  }

  const res = await fetch(`${BASE_URL}/update/${user.id}`, {
    method: 'PUT',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  console.log(data.detail)

  if (!res.ok) {
    throw new Error(data.detail || 'Error creando usuario')
  }

  if (!res.ok) throw new Error('Error creando usuario')

  return mapUserFromApi(data)
}

/* =======================
   DELETE
======================= */


/**
 * Elimina un usuario por su identificador.
 *
 * @param id Identificador único del usuario
 * @throws Error si la eliminación falla
 */
export const deleteUser = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: "include",
  })

  if (!res.ok) throw new Error('Error eliminando usuario')
}



