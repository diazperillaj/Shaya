import type { InventoryApiResponse } from '../models/types'

export const mapInventoryFromApi = (i: InventoryApiResponse) => ({
  id: i.id,

  product: i.inventory.product,
  farmer: i.farmer,

  variety: i.variety,

  elevation: Number(i.altitude),
  humidity: Number(i.humidity),

  price: Number(i.purchase_price),
  full_price: Number(i.full_price),

  quantity: Number(i.initial_quantity),
  remaining_quantity: Number(i.remaining_quantity),
  stock: Number(i.remaining_quantity),

  date: i.purchase_date,

  observation: i.inventory.observations?.trim() || 'Sin observación',
})