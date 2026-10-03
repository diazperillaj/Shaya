/**
 * Formatos de presentación del módulo de cultivo (es-CO).
 */

const EMPTY = '—'

export const fmtNumber = (value: number | null, decimals = 2, unit?: string): string => {
  if (value === null) return EMPTY
  const text = new Intl.NumberFormat('es-CO', { maximumFractionDigits: decimals }).format(value)
  return unit ? `${text} ${unit}` : text
}

export const fmtMoney = (value: number | null): string =>
  value === null
    ? EMPTY
    : new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value)

/** Fecha ISO (`2024-03-01` o con hora) a texto corto, sin correr el día por zona horaria */
export const fmtDate = (iso: string | null): string =>
  iso
    ? new Date(`${iso.slice(0, 10)}T00:00:00`).toLocaleDateString('es-CO', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : EMPTY

/** Fecha local de hoy en formato ISO, para los campos de fecha */
export const todayIso = (): string => {
  const today = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`
}

export const plural = (count: number, singular: string, pluralForm: string): string =>
  `${count} ${count === 1 ? singular : pluralForm}`

/** Densidad de siembra a partir de las distancias entre surcos y entre plantas */
export const treesPerHectare = (rowSpacing: number | null, plantSpacing: number | null): number | null =>
  rowSpacing && plantSpacing ? Math.round(10000 / (rowSpacing * plantSpacing)) : null

/** Instante ISO a fecha y hora cortas en hora local: «21 abr 2025, 5:00 p. m.» */
export const fmtDateTime = (iso: string | null): string =>
  iso
    ? new Date(iso).toLocaleString('es-CO', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : EMPTY

/** Instante ISO → valor de un campo `datetime-local` (hora local) */
export const toLocalInput = (iso: string | null): string => {
  if (!iso) return ''
  const moment = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${moment.getFullYear()}-${pad(moment.getMonth() + 1)}-${pad(moment.getDate())}T${pad(moment.getHours())}:${pad(moment.getMinutes())}`
}

/** Valor de un campo `datetime-local` → instante ISO con zona (vacío → null) */
export const fromLocalInput = (value: string): string | null =>
  value.trim() ? new Date(value).toISOString() : null
