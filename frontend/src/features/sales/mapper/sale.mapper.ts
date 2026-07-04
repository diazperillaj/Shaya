import type {
  SaleApiResponse,
  SaleDetailApiResponse,
  Sale,
  SaleDetail,
  SaleStatus,
} from '../models/types'

export const mapSaleDetailFromApi = (d: SaleDetailApiResponse): SaleDetail => ({
  id: d.id,
  sale_id: d.sale_id,
  detail_roasted_coffee_id: d.detail_roasted_coffee_id,
  detail_roasted_coffee: d.detail_roasted_coffee,
  quantity: d.quantity,
  unit_value: Number(d.unit_value),
  iva_percentage: Number(d.iva_percentage),
  subtotal: Number(d.subtotal),
  iva: Number(d.iva),
  total: Number(d.total),
})

export const mapSaleFromApi = (s: SaleApiResponse): Sale => ({
  id: s.id,
  customer_id: s.customer_id,
  customer_name: s.customer?.person?.full_name ?? '—',
  customer_type: s.customer?.customerType ?? '—',
  customer_city: s.customer?.city ?? '—',
  user_id: s.user_id,
  user_name: s.user?.person?.full_name ?? s.user?.username ?? '—',
  sale_date: s.sale_date,
  status: s.status as SaleStatus,
  observations: s.observations?.trim() || undefined,
  subtotal: Number(s.subtotal),
  iva: Number(s.iva),
  total: Number(s.total),
  details: (s.details ?? []).map(mapSaleDetailFromApi),
})
