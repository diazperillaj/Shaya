import type {
  Sale,
  SaleApiResponse,
  SaleQuery,
  CreateSalePayload,
  RoastedCoffeeProduct,
} from '../models/types'
import { mapSaleFromApi } from '../mapper/sale.mapper'
import type { Customer } from '../../customers/models/types'
import { mapCustomerFromApi } from '../../customers/mapper/customer.mapper'
import type { User } from '../../users/models/types'
import { mapUserFromApi } from '../../users/mapper/user.mapper'
import type { RoastedCoffeeApiResponse as MaquiladoApiResponse } from '../../roasted_coffee/models/types'

const SALES_URL = '/api/v1/sales'
const CUSTOMERS_URL = '/api/v1/customers'
const USERS_URL = '/api/v1/users'
const MAQUILADO_URL = '/api/v1/maquilado'

// ─── Sales CRUD ───────────────────────────────────────────────────────────────

export const fetchSales = async (filters?: SaleQuery): Promise<Sale[]> => {
  const query = new URLSearchParams()
  if (filters?.search) query.append('search', filters.search)

  const res = await fetch(`${SALES_URL}/get?${query.toString()}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error obteniendo ventas')

  const data: SaleApiResponse[] = await res.json()
  return data.map(mapSaleFromApi)
}

export const fetchSaleById = async (id: number): Promise<Sale> => {
  const res = await fetch(`${SALES_URL}/get/${id}`, {
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error obteniendo venta')

  const data: SaleApiResponse = await res.json()
  return mapSaleFromApi(data)
}

export const createSale = async (payload: CreateSalePayload): Promise<Sale> => {
  const res = await fetch(`${SALES_URL}/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error creando venta')

  return mapSaleFromApi(data)
}

export const updateSale = async (
  id: number,
  payload: CreateSalePayload,
): Promise<Sale> => {
  const res = await fetch(`${SALES_URL}/update/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Error actualizando venta')

  return mapSaleFromApi(data)
}

export const deleteSale = async (id: number): Promise<void> => {
  const res = await fetch(`${SALES_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Error eliminando venta')
}

// ─── Support data ─────────────────────────────────────────────────────────────

export const fetchSaleCustomers = async (): Promise<Customer[]> => {
  const res = await fetch(`${CUSTOMERS_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo clientes')
  const data = await res.json()
  return data.map(mapCustomerFromApi)
}

export const fetchSaleUsers = async (): Promise<User[]> => {
  const res = await fetch(`${USERS_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo usuarios')
  const data = await res.json()
  return data.map(mapUserFromApi)
}

export const fetchRoastedCoffeeInventory = async (): Promise<RoastedCoffeeProduct[]> => {
  const res = await fetch(`${MAQUILADO_URL}/get`, { credentials: 'include' })
  if (!res.ok) throw new Error('Error obteniendo inventario de café tostado')

  const data: MaquiladoApiResponse[] = await res.json()

  const products: RoastedCoffeeProduct[] = []
  for (const maquilado of data) {
    for (const p of maquilado.products) {
      products.push({
        detail_id: p.detail_id,
        roasted_coffee_id: maquilado.id,
        product_id: p.product_id,
        name: p.name,
        grams_per_bag: p.quantity,
        quantity: p.quantity,
        remaining_quantity: p.remaining_quantity,
        variety: maquilado.variety ?? undefined,
        process_id: maquilado.process_id,
      })
    }
  }

  return products.filter((p) => p.remaining_quantity > 0)
}
