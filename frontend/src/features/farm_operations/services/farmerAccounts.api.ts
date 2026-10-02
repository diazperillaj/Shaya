import type { FarmerAccount, NewFarmerAccountPayload } from '../models/types'
import { request } from './http'

export const fetchFarmerAccounts = async (): Promise<FarmerAccount[]> =>
  request<FarmerAccount[]>('/farmer-accounts/get', 'Error obteniendo las cuentas')

/** Da acceso a un caficultor ya registrado */
export const createFarmerAccount = async (payload: {
  farmer_id: number
  username: string
  password: string
}): Promise<FarmerAccount> =>
  request<FarmerAccount>('/farmer-accounts/create', 'Error creando la cuenta', {
    method: 'POST',
    body: payload,
  })

/** Registra un caficultor nuevo con su cuenta, en una sola operación */
export const createFarmerWithAccount = async (payload: NewFarmerAccountPayload): Promise<FarmerAccount> =>
  request<FarmerAccount>('/farmer-accounts/create-full', 'Error registrando el caficultor', {
    method: 'POST',
    body: payload,
  })
