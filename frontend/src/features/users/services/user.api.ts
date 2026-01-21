import type { User, UsersQuery } from '../models/types'
import { mapUserFromApi } from '../mapper/user.mapper'


const BASE_URL = 'http://localhost:8000/api/v1/users'

/* =======================
   GET
======================= */
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
  return data.map(mapUserFromApi)
}

/* =======================
   CREATE
======================= */
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

  if (!res.ok) throw new Error('Error actualizando usuario')

  return mapUserFromApi(await res.json())
}

/* =======================
   DELETE
======================= */

export const deleteUser = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: "include",
  })

  if (!res.ok) throw new Error('Error eliminando usuario')
}



