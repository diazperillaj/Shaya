// ─── Sale status ─────────────────────────────────────────────────────────────

export type SaleStatus = 'in_progress' | 'completed'

// ─── Nested API shapes ────────────────────────────────────────────────────────

export interface PersonApi {
  id: number
  full_name: string
}

export interface CustomerApi {
  id: number
  customerType: string
  city: string
  person: PersonApi
}

export interface UserApi {
  id: number
  username: string
  role: string
  person: PersonApi
}

export interface ProductApi {
  id: number
  name: string
  quantity: number // grams per bag
}

export interface PaymentMethodApi {
  id: number
  name: string
}

export interface DetailRoastedCoffeeApi {
  id: number
  roasted_coffee_id: number
  product_id: number
  product?: ProductApi
  quantity: number
  remaining_quantity: number
}

// ─── Detail sale ──────────────────────────────────────────────────────────────

export interface SaleDetail {
  id: number
  sale_id: number
  detail_roasted_coffee_id: number
  detail_roasted_coffee?: DetailRoastedCoffeeApi
  quantity: number
  unit_value: number
  iva_percentage: number
  subtotal: number
  iva: number
  total: number
}

export interface SaleDetailApiResponse {
  id: number
  sale_id: number
  detail_roasted_coffee_id: number
  detail_roasted_coffee?: DetailRoastedCoffeeApi
  quantity: number
  unit_value: string
  iva_percentage: string
  subtotal: string
  iva: string
  total: string
}

// ─── Sale ─────────────────────────────────────────────────────────────────────

export interface Sale {
  id: number
  customer_id: number
  customer_name: string
  customer_type: string
  customer_city: string
  user_id: number
  user_name: string
  payment_method_id?: number
  payment_method_name: string
  sale_date: string
  status: SaleStatus
  observations?: string
  subtotal: number
  iva: number
  total: number
  details: SaleDetail[]
}

export interface SaleApiResponse {
  id: number
  customer_id: number
  customer?: CustomerApi
  user_id: number
  user?: UserApi
  payment_method_id?: number | null
  payment_method?: PaymentMethodApi | null
  sale_date: string
  status: string
  observations?: string
  subtotal: string
  iva: string
  total: string
  details: SaleDetailApiResponse[]
}

// ─── Inventory option (for the product select in the form) ───────────────────

export interface RoastedCoffeeProduct {
  detail_id: number        // detail_roasted_coffee.id
  roasted_coffee_id: number
  product_id: number
  name: string
  grams_per_bag: number
  quantity: number         // total bags produced
  remaining_quantity: number
  variety?: string
  process_id: number
}

// ─── Query ────────────────────────────────────────────────────────────────────

export interface SaleQuery {
  search?: string
}

// ─── Create / update payloads ────────────────────────────────────────────────

export interface CreateSaleDetailPayload {
  detail_roasted_coffee_id: number
  quantity: number
  unit_value: number
  iva_percentage: number
}

export interface CreateSalePayload {
  customer_id: number
  user_id?: number          // admin only
  payment_method_id: number
  sale_date: string
  status: SaleStatus
  observations?: string
  details: CreateSaleDetailPayload[]
}
