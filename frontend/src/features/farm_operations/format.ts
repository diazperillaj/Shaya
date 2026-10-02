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
