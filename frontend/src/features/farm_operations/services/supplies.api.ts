import type { Supply, SupplyPayload, SupplyType } from '../models/types'
import { request } from './http'

export const fetchSupplies = async (filters: {
  supply_type?: SupplyType
  search?: string
  active?: boolean
} = {}): Promise<Supply[]> =>
  request<Supply[]>('/supplies/get', 'Error obteniendo los insumos', { query: filters })

export const createSupply = async (payload: SupplyPayload): Promise<Supply> =>
  request<Supply>('/supplies/create', 'Error creando el insumo', { method: 'POST', body: payload })

export const updateSupply = async (id: number, payload: SupplyPayload): Promise<Supply> =>
  request<Supply>(`/supplies/update/${id}`, 'Error actualizando el insumo', {
    method: 'PUT',
    body: payload,
  })

export const setSupplyActive = async (id: number, active: boolean): Promise<Supply> =>
  request<Supply>(
    `/supplies/${id}/${active ? 'activate' : 'deactivate'}`,
    active ? 'Error activando el insumo' : 'Error desactivando el insumo',
    { method: 'POST' },
  )

export const deleteSupply = async (id: number): Promise<void> => {
  await request(`/supplies/delete/${id}`, 'Error eliminando el insumo', { method: 'DELETE' })
}
