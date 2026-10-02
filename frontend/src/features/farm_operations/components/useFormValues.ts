import { useState } from 'react'

/**
 * Estado de un formulario cuyos campos se editan como texto.
 *
 * Cada campo guarda lo que hay en el input y se convierte al enviar: un
 * campo vacío se envía como `null`, nunca como 0.
 */
export function useFormValues<K extends string>(initial: Record<K, string>) {
  const [values, setValues] = useState(initial)
  const [errors, setErrors] = useState<Partial<Record<K, string>>>({})

  /** Props de un campo: valor, cambio y error (el error se limpia al editar) */
  const bind = (key: K) => ({
    value: values[key],
    error: errors[key],
    onChange: (value: string) => {
      setValues((prev) => ({ ...prev, [key]: value }))
      setErrors((prev) => ({ ...prev, [key]: undefined }))
    },
  })

  /** Marca los campos obligatorios vacíos. Devuelve true si están todos */
  const requireFields = (keys: K[]): boolean => {
    const missing = keys.filter((key) => !values[key].trim())
    if (missing.length > 0) {
      setErrors((prev) => {
        const next = { ...prev }
        missing.forEach((key) => { next[key] = 'Campo obligatorio' })
        return next
      })
    }
    return missing.length === 0
  }

  /** Marca un error en un campo (validaciones propias del formulario) */
  const setFieldError = (key: K, message: string) =>
    setErrors((prev) => ({ ...prev, [key]: message }))

  return { values, bind, requireFields, setFieldError }
}

/** Texto del formulario a valor de la API: vacío → null */
export const textOrNull = (value: string): string | null => value.trim() || null

/** Número del formulario a valor de la API: vacío → null */
export const numberOrNull = (value: string): number | null =>
  value.trim() === '' ? null : Number(value)

/** Valor de la API a texto del formulario */
export const toInput = (value: string | number | null | undefined): string =>
  value === null || value === undefined ? '' : String(value)
