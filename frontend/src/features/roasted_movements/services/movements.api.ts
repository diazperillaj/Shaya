import type { RoastedMovement, RoastedMovementCreate } from '../models/types'

const BASE_URL = '/api/v1/roasted-movements'

export const fetchMovements = async (): Promise<RoastedMovement[]> => {
  const res = await fetch(`${BASE_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo movimientos')
  return res.json()
}

export const createMovement = async (payload: RoastedMovementCreate): Promise<RoastedMovement> => {
  const res = await fetch(`${BASE_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Error al crear el movimiento')
  }
  return res.json()
}

export const deleteMovement = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Error al eliminar el movimiento')
  }
}
