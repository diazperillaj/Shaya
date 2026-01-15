import type { User } from '../models/types'
import { mapUserFromApi } from '../mapper/user.mapper'

const BASE_URL = 'http://localhost:8000/api/v1/users'

/* =======================
   GET
======================= */
export const fetchUsers = async (): Promise<User[]> => {
  const res = await fetch(`${BASE_URL}/get`)
  const data = await res.json()
  return data.map(mapUserFromApi)
}

/* =======================
   CREATE
======================= */
export const createUser = async (user: User): Promise<User> => {
  const payload = {
    username: user.username,
    hashed_password: user.password,
    role: user.role || 'user',
    person: {
      full_name: user.name,
      document: user.document,
      email: user.email,
      phone: user.phone,
      observation: user.observation,
    },
  }

  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) throw new Error('Error creando usuario')

  alert('Usuario creado correctamente')

  return mapUserFromApi(await res.json())
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) throw new Error('Error actualizando usuario')

  alert('Usuario actualizado correctamente')

  return mapUserFromApi(await res.json())
}

/* =======================
   DELETE
======================= */

export const deleteUser = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
  })

  if (!res.ok) throw new Error('Error eliminando usuario')
}
