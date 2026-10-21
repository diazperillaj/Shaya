// src/features/roasted_coffee/models/columns.tsx
import type { ColumnDef } from '@tanstack/react-table'
import { fmtShortDate, fmtUnits, KIND_LABEL } from './inventory'
import type { InventoryEvent, InventoryLot } from './types'

/** Una fila por producto de cada lote, con existencias o agotado */
export interface LotHistoryRow {
  detail_id: number
  lot_id: number
  invoice_number: string
  process_date: string
  variety: string
  farmer: string
  product_name: string
  total_in: number
  total_out: number
  remaining_quantity: number
}

export const toLotHistoryRows = (lots: InventoryLot[]): LotHistoryRow[] =>
  lots.flatMap((lot) =>
    lot.products.map((p) => ({
      detail_id: p.detail_id,
      lot_id: lot.id,
      invoice_number: lot.invoice_number,
      process_date: lot.process_date,
      variety: lot.variety || 'Sin variedad',
      farmer: lot.farmer_name || 'Sin caficultor',
      product_name: p.name,
      total_in: p.total_in,
      total_out: p.total_out,
      remaining_quantity: p.remaining_quantity,
    })),
  )

const CHIP = 'inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium'

export const LotHistoryColumns: ColumnDef<LotHistoryRow>[] = [
  {
    accessorKey: 'lot_id',
    header: 'Lote',
    cell: ({ row }) => (
      <div className="flex flex-col">
        <span className="font-medium text-gray-900">#{row.original.lot_id}</span>
        <span className="text-xs text-gray-400">Factura {row.original.invoice_number}</span>
      </div>
    ),
    meta: { narrow: true, align: 'left' },
  },
  {
    accessorKey: 'process_date',
    header: 'Proceso',
    cell: (info) => fmtShortDate(info.getValue() as string),
    meta: { narrow: true },
  },
  { accessorKey: 'variety', header: 'Variedad' },
  { accessorKey: 'farmer', header: 'Caficultor' },
  { accessorKey: 'product_name', header: 'Producto' },
  {
    accessorKey: 'total_in',
    header: 'Entró',
    cell: (info) => fmtUnits(info.getValue() as number),
    meta: { narrow: true },
  },
  {
    accessorKey: 'total_out',
    header: 'Salió',
    cell: (info) => fmtUnits(info.getValue() as number),
    meta: { narrow: true },
  },
  {
    accessorKey: 'remaining_quantity',
    header: 'Disponible',
    cell: (info) => <span className="font-semibold text-gray-900">{fmtUnits(info.getValue() as number)}</span>,
    meta: { narrow: true },
  },
  {
    id: 'status',
    header: 'Estado',
    accessorFn: (row) => (row.remaining_quantity > 0 ? 'Disponible' : 'Agotado'),
    cell: (info) =>
      info.getValue() === 'Disponible' ? (
        <span className={`${CHIP} bg-emerald-100 text-emerald-800`}>Disponible</span>
      ) : (
        <span className={`${CHIP} bg-gray-100 text-gray-500`}>Agotado</span>
      ),
    meta: { narrow: true },
  },
]

/** Nombre del tipo de evento; los movimientos dicen si entraron o salieron */
export const eventLabel = (e: InventoryEvent) =>
  e.kind === 'movement' ? `Movimiento · ${e.quantity > 0 ? 'entrada' : 'salida'}` : KIND_LABEL[e.kind]

export const EventColumns: ColumnDef<InventoryEvent>[] = [
  {
    accessorKey: 'event_date',
    header: 'Fecha',
    cell: (info) => fmtShortDate(info.getValue() as string),
    meta: { narrow: true },
  },
  {
    accessorKey: 'lot_id',
    header: 'Lote',
    cell: (info) => `#${info.getValue()}`,
    meta: { narrow: true, align: 'left' },
  },
  { accessorKey: 'product_name', header: 'Producto' },
  {
    id: 'kind',
    header: 'Tipo',
    accessorFn: eventLabel,
    cell: (info) => <span className={`${CHIP} bg-gray-100 text-gray-700`}>{info.getValue() as string}</span>,
    meta: { narrow: true },
  },
  { accessorKey: 'reference', header: 'Referencia' },
  {
    accessorKey: 'note',
    header: 'Detalle',
    cell: (info) => <span className="line-clamp-2 text-gray-500">{(info.getValue() as string | null) ?? '—'}</span>,
  },
  {
    accessorKey: 'quantity',
    header: 'Cantidad',
    cell: (info) => {
      const value = info.getValue() as number
      return value > 0 ? (
        <span className="font-semibold tabular-nums text-emerald-700">+{fmtUnits(value)}</span>
      ) : (
        <span className="font-semibold tabular-nums text-gray-900">−{fmtUnits(-value)}</span>
      )
    },
    meta: { narrow: true },
  },
]
