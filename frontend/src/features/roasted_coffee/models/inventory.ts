/**
 * Cálculos del tablero de maquilado a partir de los lotes y la línea de
 * tiempo de entradas (+) y salidas (−) que envía el backend.
 */
import type { RechartsDataPoint } from '../../../components/charts/chartData'
import type { InventoryEvent, InventoryEventKind, InventoryLot, InventoryLotProduct } from './types'

// ─── Formatos ────────────────────────────────────────────────────────────────

export const fmtUnits = (n: number) => n.toLocaleString('es-CO', { maximumFractionDigits: 1 })

export const bags = (n: number) => `${fmtUnits(n)} ${n === 1 ? 'bolsa' : 'bolsas'}`

/** Fecha ISO a texto corto, sin correr el día por zona horaria */
export const fmtDate = (iso: string) =>
  toDay(iso).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })

/** Fecha ISO para tablas: «5 jun 2026» */
export const fmtShortDate = (iso: string) => {
  const day = toDay(iso)
  const month = day.toLocaleDateString('es-CO', { month: 'short' }).replace('.', '')
  return `${day.getDate()} ${month} ${day.getFullYear()}`
}

const DAY_MS = 86_400_000
const toDay = (iso: string) => new Date(`${iso.slice(0, 10)}T00:00:00`)

export const startOfToday = () => {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

export const daysSince = (iso: string, today: Date) =>
  Math.max(0, Math.round((today.getTime() - toDay(iso).getTime()) / DAY_MS))

// ─── Tipos de evento ─────────────────────────────────────────────────────────

export const KIND_LABEL: Record<InventoryEventKind, string> = {
  process: 'Entrada del proceso',
  sale: 'Venta',
  fair: 'Feria',
  movement: 'Movimiento',
  adjustment: 'Ajuste',
}

/** Por dónde salen las unidades; el orden fija el color de cada canal */
export const CHANNELS: { kind: InventoryEventKind; label: string }[] = [
  { kind: 'sale', label: 'Ventas' },
  { kind: 'fair', label: 'Ferias' },
  { kind: 'movement', label: 'Movimientos' },
  { kind: 'adjustment', label: 'Ajustes' },
]

/**
 * Colores de identidad (productos, canales), en orden fijo. Validados para
 * daltonismo sobre las superficies clara (#ffffff) y oscura (#161c19).
 */
export const SERIES_COLORS = ['#059669', '#ea580c', '#2a78d6', '#c98500', '#9085e9', '#e11d48']
export const OTHER_COLOR = '#9ca3af'
export const OTHERS = 'Otros'

// ─── Inventario actual ───────────────────────────────────────────────────────

/** Lote con unidades disponibles: solo sus productos con existencias */
export interface StockLot extends InventoryLot {
  available: InventoryLotProduct[]
  remaining: number
  /** Valor a costo de producción; null si ningún producto tiene costo */
  value: number | null
  ageDays: number
}

export function stockLots(lots: InventoryLot[], today: Date): StockLot[] {
  return lots
    .map((lot) => {
      const available = lot.products.filter((p) => p.remaining_quantity > 0)
      const costed = available.filter((p) => p.unit_cost !== null)
      return {
        ...lot,
        available,
        remaining: sum(available.map((p) => p.remaining_quantity)),
        value: costed.length ? sum(costed.map((p) => p.remaining_quantity * (p.unit_cost ?? 0))) : null,
        ageDays: daysSince(lot.process_date, today),
      }
    })
    .filter((lot) => lot.available.length > 0)
    .sort((a, b) => b.process_date.localeCompare(a.process_date) || b.id - a.id)
}

/** Búsqueda por lote, factura, variedad, caficultor, finca o producto */
export function matchesLot(lot: InventoryLot, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return [
    `#${lot.id}`,
    String(lot.id),
    lot.invoice_number,
    lot.variety ?? '',
    lot.farmer_name ?? '',
    lot.farm_name ?? '',
    ...lot.products.map((p) => p.name),
  ].some((text) => text.toLowerCase().includes(q))
}

// ─── Indicadores ─────────────────────────────────────────────────────────────

export interface InventoryKpis {
  available: number
  lots: number
  products: number
  value: number
  /** Productos con existencias pero sin costo calculado */
  uncosted: number
  exits30: number
  exitsPrev30: number
  /** Bolsas por día, promedio de los últimos 90 días */
  dailyRate: number
  coverageDays: number | null
  avgAgeDays: number | null
  oldest: { lotId: number; days: number } | null
  totalIn: number
  totalOut: number
}

const isExit = (e: InventoryEvent) => e.quantity < 0

/** Salidas entre `fromDays` y `toDays` días atrás (incluye hoy si toDays = 0) */
function exitsBetween(events: InventoryEvent[], today: Date, fromDays: number, toDays: number) {
  return sum(
    events
      .filter(isExit)
      .filter((e) => {
        const age = (today.getTime() - toDay(e.event_date).getTime()) / DAY_MS
        return age >= toDays && age < fromDays
      })
      .map((e) => -e.quantity),
  )
}

export function inventoryKpis(lots: InventoryLot[], stock: StockLot[], events: InventoryEvent[], today: Date): InventoryKpis {
  const inStock = stock.flatMap((lot) => lot.available)
  const available = sum(inStock.map((p) => p.remaining_quantity))
  const dailyRate = exitsBetween(events, today, 90, 0) / 90
  const oldest = stock.reduce<StockLot | null>((max, lot) => (!max || lot.ageDays > max.ageDays ? lot : max), null)
  const allProducts = lots.flatMap((lot) => lot.products)

  return {
    available,
    lots: stock.length,
    products: new Set(inStock.map((p) => p.product_id)).size,
    value: sum(inStock.map((p) => p.remaining_quantity * (p.unit_cost ?? 0))),
    uncosted: inStock.filter((p) => p.unit_cost === null).length,
    exits30: exitsBetween(events, today, 30, 0),
    exitsPrev30: exitsBetween(events, today, 60, 30),
    dailyRate,
    coverageDays: dailyRate > 0 ? available / dailyRate : null,
    avgAgeDays: available > 0 ? sum(stock.map((lot) => lot.ageDays * lot.remaining)) / available : null,
    oldest: oldest ? { lotId: oldest.id, days: oldest.ageDays } : null,
    totalIn: sum(allProducts.map((p) => p.total_in)),
    totalOut: sum(allProducts.map((p) => p.total_out)),
  }
}

// ─── Gráficas ────────────────────────────────────────────────────────────────

const MONTHS = 12
const monthKey = (iso: string) => iso.slice(0, 7)

/** «2026-06» → «jun 26» */
function monthLabel(key: string) {
  const [year, month] = key.split('-').map(Number)
  const name = new Date(year, month - 1, 1).toLocaleDateString('es-CO', { month: 'short' }).replace('.', '')
  return `${name} ${String(year).slice(2)}`
}

/**
 * Últimos 12 meses hasta el mes actual (o hasta el último evento, si alguno
 * quedó con fecha posterior), sin empezar antes del primer evento.
 */
export function monthWindow(events: InventoryEvent[], today: Date): string[] {
  if (events.length === 0) return []
  const current = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
  const last = monthKey(events[events.length - 1].event_date)
  const first = monthKey(events[0].event_date)
  const end = last > current ? last : current

  const keys: string[] = []
  let [year, month] = end.split('-').map(Number)
  for (let i = 0; i < MONTHS; i++) {
    const key = `${year}-${String(month).padStart(2, '0')}`
    if (key < first) break
    keys.unshift(key)
    month -= 1
    if (month === 0) {
      month = 12
      year -= 1
    }
  }
  return keys
}

/**
 * Productos con color propio: los seis con más salidas en toda la
 * historia, así un producto conserva su color mes a mes. El resto va a «Otros».
 */
export function productSeries(events: InventoryEvent[]): Map<string, string> {
  const totals = new Map<string, number>()
  for (const e of events.filter(isExit)) {
    totals.set(e.product_name, (totals.get(e.product_name) ?? 0) - e.quantity)
  }
  const ranked = [...totals.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
  return new Map(ranked.slice(0, SERIES_COLORS.length).map(([name], i) => [name, SERIES_COLORS[i]]))
}

/**
 * Unidades que salieron cada mes, apiladas por producto. Los productos sin
 * color propio van juntos en «Otros»; si es uno solo, conserva su nombre.
 */
export function exitsByProduct(events: InventoryEvent[], months: string[], series: Map<string, string>) {
  const exits = events.filter((e) => isExit(e) && months.includes(monthKey(e.event_date)))
  const leftovers = new Set(exits.map((e) => e.product_name).filter((name) => !series.has(name)))
  const othersKey = leftovers.size === 1 ? [...leftovers][0] : OTHERS

  const rows = new Map(months.map((key) => [key, {} as Record<string, number>]))
  for (const e of exits) {
    const row = rows.get(monthKey(e.event_date))!
    const name = series.has(e.product_name) ? e.product_name : othersKey
    row[name] = (row[name] ?? 0) - e.quantity
  }
  const keys = [...series.keys()].filter((name) => months.some((m) => rows.get(m)?.[name]))
  if (leftovers.size > 0) keys.push(othersKey)
  const data: RechartsDataPoint[] = months.map((key) => {
    const row = rows.get(key) ?? {}
    return { name: monthLabel(key), ...Object.fromEntries(keys.map((k) => [k, row[k] ?? 0])) }
  })
  return { data, keys, othersKey }
}

/**
 * Entradas, salidas y existencias al cierre de cada mes. Las existencias se
 * suman producto por producto sin bajar de cero: en datos importados hay
 * ventas registradas antes que la entrada de su lote, y un saldo negativo
 * no es inventario.
 */
export function monthlyFlow(events: InventoryEvent[], months: string[]): RechartsDataPoint[] {
  if (months.length === 0) return []
  const balance = new Map<number, number>()
  const apply = (e: InventoryEvent) => balance.set(e.detail_id, (balance.get(e.detail_id) ?? 0) + e.quantity)
  events.filter((e) => monthKey(e.event_date) < months[0]).forEach(apply)

  return months.map((key) => {
    const inMonth = events.filter((e) => monthKey(e.event_date) === key)
    inMonth.forEach(apply)
    return {
      name: monthLabel(key),
      Entradas: sum(inMonth.filter((e) => e.quantity > 0).map((e) => e.quantity)),
      Salidas: -sum(inMonth.filter(isExit).map((e) => e.quantity)),
      Existencias: sum([...balance.values()].map((b) => Math.max(0, b))),
    }
  })
}

/** Salidas del periodo por canal (ventas, ferias, movimientos…) */
export function exitsByChannel(events: InventoryEvent[], months: string[]) {
  const inWindow = events.filter((e) => isExit(e) && months.includes(monthKey(e.event_date)))
  return CHANNELS.map((channel, i) => ({
    name: channel.label,
    value: -sum(inWindow.filter((e) => e.kind === channel.kind).map((e) => e.quantity)),
    color: SERIES_COLORS[i],
  })).filter((slice) => slice.value > 0)
}

export interface StockBar {
  name: string
  value: number
}

/** Existencias agrupadas y ordenadas de mayor a menor */
function groupStock(stock: StockLot[], keyOf: (lot: StockLot, product: InventoryLotProduct) => string): StockBar[] {
  const totals = new Map<string, number>()
  for (const lot of stock) {
    for (const product of lot.available) {
      const key = keyOf(lot, product)
      totals.set(key, (totals.get(key) ?? 0) + product.remaining_quantity)
    }
  }
  return [...totals.entries()]
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value || a.name.localeCompare(b.name))
}

export const stockByProduct = (stock: StockLot[]) => groupStock(stock, (_, product) => product.name)

export const stockByVariety = (stock: StockLot[]) => groupStock(stock, (lot) => lot.variety || 'Sin variedad')

export const stockByFarmer = (stock: StockLot[]) => groupStock(stock, (lot) => lot.farmer_name || 'Sin caficultor')

/** Rangos de antigüedad desde la fecha del proceso */
const AGE_BANDS: { label: string; max: number }[] = [
  { label: '0–30 días', max: 30 },
  { label: '31–60 días', max: 60 },
  { label: '61–90 días', max: 90 },
  { label: '91–180 días', max: 180 },
  { label: 'Más de 180', max: Infinity },
]

export function stockByAge(stock: StockLot[]): StockBar[] {
  return AGE_BANDS.map((band, i) => ({
    name: band.label,
    value: sum(
      stock
        .filter((lot) => lot.ageDays <= band.max && (i === 0 || lot.ageDays > AGE_BANDS[i - 1].max))
        .map((lot) => lot.remaining),
    ),
  }))
}

function sum(values: number[]) {
  return values.reduce((total, v) => total + v, 0)
}
