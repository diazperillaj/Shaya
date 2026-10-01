/**
 * Error de validación tal como lo devuelve FastAPI en un 422.
 */
interface ValidationIssue {
  type?: string
  loc?: (string | number)[]
  msg?: string
  ctx?: Record<string, unknown>
}

/**
 * Traducción de los tipos de error de validación más comunes.
 * Los demás se muestran con el mensaje original de la API.
 */
const VALIDATION_MESSAGES: Partial<
  Record<string, (ctx: Record<string, unknown>) => string>
> = {
  missing: () => 'es obligatorio',
  int_parsing: () => 'debe ser un número entero',
  int_from_float: () => 'debe ser un número entero',
  float_parsing: () => 'debe ser un número',
  decimal_parsing: () => 'debe ser un número',
  greater_than: (ctx) => `debe ser mayor que ${ctx.gt}`,
  greater_than_equal: (ctx) => `debe ser mayor o igual a ${ctx.ge}`,
  less_than: (ctx) => `debe ser menor que ${ctx.lt}`,
  less_than_equal: (ctx) => `debe ser menor o igual a ${ctx.le}`,
  string_too_short: (ctx) => `debe tener al menos ${ctx.min_length} caracteres`,
  string_too_long: (ctx) => `debe tener máximo ${ctx.max_length} caracteres`,
  date_parsing: () => 'debe ser una fecha válida',
  datetime_parsing: () => 'debe ser una fecha y hora válida',
  enum: () => 'no es una opción válida',
}

/**
 * Describe un error de validación como `campo: mensaje`.
 */
const describeIssue = (issue: unknown): string => {
  if (typeof issue === 'string') return issue
  if (typeof issue !== 'object' || issue === null) return 'valor inválido'

  const { type, loc, msg, ctx } = issue as ValidationIssue
  const translate = type ? VALIDATION_MESSAGES[type] : undefined
  // Los validadores propios del backend ya escriben su mensaje en español.
  const message = translate
    ? translate(ctx ?? {})
    : (msg ?? 'valor inválido').replace(/^Value error, /, '')

  const field = (loc ?? []).filter((part) => part !== 'body').join('.')
  return field ? `${field}: ${message}` : message
}

/**
 * Obtiene un mensaje legible del cuerpo de una respuesta de error de la API.
 *
 * El backend responde `detail` como texto en los errores de negocio y como
 * lista de errores en los de validación (422). Sin un detalle útil se usa
 * el mensaje por defecto.
 *
 * @param body Cuerpo de la respuesta ya convertido desde JSON
 * @param fallback Mensaje por defecto, que describe la operación que falló
 */
export const apiErrorMessage = (body: unknown, fallback: string): string => {
  const detail =
    typeof body === 'object' && body !== null
      ? (body as { detail?: unknown }).detail
      : undefined

  if (typeof detail === 'string' && detail.trim()) return detail

  if (Array.isArray(detail) && detail.length > 0) {
    const issues = detail.map((issue) => `- ${describeIssue(issue)}`)
    return `${fallback}:\n${issues.join('\n')}`
  }

  return fallback
}
