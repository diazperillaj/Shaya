import type { User } from '../models/types'
import { mapUserFromApi } from '../mapper/user.mapper'

const BASE_URL = 'http://localhost:8000/api/v1/users'

export const fetchUsers = async (): Promise<User[]> => {
  const res = await fetch(`${BASE_URL}/get/users`)
  const data = await res.json()
  return data.map(mapUserFromApi)
}

export const createUser = async (user: User): Promise<User> => {
  const payload = {
    username: user.username,
    hashed_password: user.hashed_password,
    role: user.role || 'user',
    person: {
      full_name: user.name,
      document: user.document,
      email: user.email,
      phone: user.phone,
      observation: user.observation,
    },
  }

  const res = await fetch(`${BASE_URL}/create/user`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) throw new Error('Error creando usuario')

  return mapUserFromApi(await res.json())
}
