import { apiErrorMessage } from '../../../utils/apiError'

/** Prefijo de la API del módulo de cultivo */
const FARM_API = '/api/v1/farm'

type QueryValue = string | number | boolean | null | undefined

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: unknown
  /** Parámetros de consulta; los vacíos se omiten */
  query?: Record<string, QueryValue>
}

/**
 * Llama a la API del módulo de cultivo con la cookie de sesión.
 *
 * @param path Ruta dentro del módulo (p. ej. `/farms/get`)
 * @param fallback Mensaje de error si la respuesta no trae detalle
 * @throws Error con un mensaje legible si la respuesta no es exitosa
 */
export async function request<T>(
  path: string,
  fallback: string,
  { method = 'GET', body, query }: RequestOptions = {},
): Promise<T> {
  const params = new URLSearchParams()
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, String(value))
    }
  })
  const search = params.toString()

  const res = await fetch(`${FARM_API}${path}${search ? `?${search}` : ''}`, {
    method,
    credentials: 'include',
    ...(body !== undefined && {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  })

  const data = await res.json().catch(() => null)
  if (!res.ok) throw new Error(apiErrorMessage(data, fallback))
  return data as T
}

/** Convierte un decimal de la API (texto) a número, conservando `null` */
export const toNumber = (value: string | number | null | undefined): number | null =>
  value === null || value === undefined || value === '' ? null : Number(value)

/**
 * Copia un objeto de la API convirtiendo a número sus campos decimales
 * (que llegan como texto). Para respuestas con muchos decimales.
 */
export function withNumbers<T>(raw: unknown, fields: readonly string[]): T {
  const record = { ...(raw as Record<string, unknown>) }
  fields.forEach((field) => {
    if (field in record) record[field] = toNumber(record[field] as string | null)
  })
  return record as T
}
