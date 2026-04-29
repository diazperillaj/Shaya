// features/inventoryProcessed/mapper/inventoryProcessed.mapper.ts

import type {
  ProcessApiResponse,
  ProcessDetailApiResponse,
  Process,
  ProcessDetail,
} from '../models/types'

export const mapProcesoFromApi = (p: ProcessApiResponse): Process => ({
  id: p.id,
  invoice_number: p.invoice_number,
  process_date: p.process_date,
  parchment_id: p.parchment_id,
  parchment_kg: Number(p.parchment_kg),
  resultant_kg: Number(p.resultant_kg),
  yield_percentage: Number(p.yield_percentage),
  subtotal: Number(p.subtotal),
  iva: Number(p.iva),
  total: Number(p.total),
  observations: p.observations?.trim() || undefined,
})

export const mapDetalleFromApi = (d: ProcessDetailApiResponse): ProcessDetail => ({
  id: d.id,
  p_id: d.process_id,
  process_date  : d.date,
  product_id: d.product_id,
  bag_quantity: d.bag_quantity,
  grams_per_bag: d.grams_per_bag,
  unit_value: Number(d.unit_value),
  iva: Number(d.iva),
  total: Number(d.total),
  observations: d.observations?.trim() || undefined,
})