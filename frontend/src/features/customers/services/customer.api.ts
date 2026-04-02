import type { Customer, CustomersQuery } from '../models/types'
import { mapCustomerFromApi } from '../mapper/customer.mapper'


const BASE_URL = 'http://localhost:8000/api/v1/customers'

/* =======================
   GET
======================= */
export const fetchCustomers = async (filters?: CustomersQuery): Promise<Customer[]> => {
  const query = new URLSearchParams()

  if (filters?.search) query.append('search', filters?.search)

  const res = await fetch(`${BASE_URL}/get?${query.toString()}`,
    {
      credentials: 'include',
    })
  if (!res.ok) throw new Error('Error obteniendo clientes')

  const data = await res.json()

  console.log(data)

  return data.map(mapCustomerFromApi)
}

/* =======================
   CREATE
======================= */
export const createCustomer = async (Customer: Customer): Promise<Customer> => {
  const payload = {
    customerType: Customer.customerType  || 'Minorista',
    address: Customer.address,
    city: Customer.city,
    person: {
      full_name: Customer.name,
      document: Customer.document,
      email: Customer.email,
      phone: Customer.phone,
      observation: Customer.observation,
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

  


  if (!res.ok) {
    throw new Error(data.detail || 'Error creando cliente')
  }

  if (!res.ok) throw new Error('Error creando cliente')

  return mapCustomerFromApi(data)
}

/* =======================
   UPDATE
======================= */
export const updateCustomer = async (Customer: Customer): Promise<Customer> => {
  const payload: any = {
    customerType: Customer.customerType || 'Minorista',
    address: Customer.address,
    city: Customer.city,
    person: {
      full_name: Customer.name,
      document: Customer.document,
      email: Customer.email,
      phone: Customer.phone,
      observation: Customer.observation,
    },
  }

  const res = await fetch(`${BASE_URL}/update/${Customer.id}`, {
    method: 'PUT',
    credentials: "include",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()

  console.log(data.detail)

  if (!res.ok) {
    throw new Error(data.detail || 'Error creando cliente')
  }

  if (!res.ok) throw new Error('Error creando cliente')

  return mapCustomerFromApi(data)
}

/* =======================
   DELETE
======================= */

export const deleteCustomer = async (id: number): Promise<void> => {
  const res = await fetch(`${BASE_URL}/delete/${id}`, {
    method: 'DELETE',
    credentials: "include",
  })

  if (!res.ok) throw new Error('Error eliminando cliente')
}



