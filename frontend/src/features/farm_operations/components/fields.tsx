import { useId } from 'react'
import type { ReactNode } from 'react'
import { inputClass } from './styles'

/**
 * Campos de formulario del módulo de cultivo.
 *
 * Todos son controlados con valores de texto (ver `useFormValues`) y
 * muestran su error o una ayuda debajo del campo.
 */

interface BaseFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  error?: string
  required?: boolean
  hint?: string
  placeholder?: string
  /** Ocupa las dos columnas de la sección */
  wide?: boolean
}

/** Etiqueta, error o ayuda alrededor de un control de formulario */
export function FieldShell({
  id,
  label,
  required,
  error,
  hint,
  wide,
  children,
}: Pick<BaseFieldProps, 'label' | 'required' | 'error' | 'hint' | 'wide'> & {
  id: string
  children: ReactNode
}) {
  return (
    <div className={`flex flex-col gap-1.5 ${wide ? 'sm:col-span-2' : ''}`}>
      <label htmlFor={id} className="text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-600"> *</span>}
      </label>
      {children}
      {error ? (
        <p className="text-xs text-red-600">{error}</p>
      ) : (
        hint && <p className="text-xs text-gray-400">{hint}</p>
      )}
    </div>
  )
}

export function TextField({
  type = 'text',
  suggestions,
  ...props
}: BaseFieldProps & { type?: 'text' | 'password' | 'email' | 'tel'; suggestions?: string[] }) {
  const id = useId()
  return (
    <FieldShell id={id} {...props}>
      <input
        id={id}
        type={type}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        placeholder={props.placeholder}
        list={suggestions ? `${id}-suggestions` : undefined}
        autoComplete={type === 'password' ? 'new-password' : 'off'}
        className={inputClass(props.error)}
      />
      {suggestions && (
        <datalist id={`${id}-suggestions`}>
          {suggestions.map((option) => <option key={option} value={option} />)}
        </datalist>
      )}
    </FieldShell>
  )
}

export function NumberField({
  step = '1',
  min,
  unit,
  ...props
}: BaseFieldProps & { step?: string; min?: string; unit?: string }) {
  const id = useId()
  return (
    <FieldShell id={id} {...props}>
      <div className="relative">
        <input
          id={id}
          type="number"
          inputMode={step === '1' ? 'numeric' : 'decimal'}
          step={step}
          min={min}
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder={props.placeholder}
          className={`${inputClass(props.error)} ${unit ? 'pr-16' : ''}`}
        />
        {unit && (
          <span className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-xs text-gray-400">
            {unit}
          </span>
        )}
      </div>
    </FieldShell>
  )
}

export function DateField({ max, ...props }: BaseFieldProps & { max?: string }) {
  const id = useId()
  return (
    <FieldShell id={id} {...props}>
      <input
        id={id}
        type="date"
        max={max}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        className={inputClass(props.error)}
      />
    </FieldShell>
  )
}

export function SelectField({
  options,
  ...props
}: BaseFieldProps & { options: { value: string; label: string }[] }) {
  const id = useId()
  return (
    <FieldShell id={id} {...props}>
      <select
        id={id}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        className={inputClass(props.error)}
      >
        {props.placeholder && <option value="">{props.placeholder}</option>}
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </FieldShell>
  )
}

export function TextAreaField(props: BaseFieldProps & { rows?: number }) {
  const id = useId()
  return (
    <FieldShell id={id} {...props} wide>
      <textarea
        id={id}
        rows={props.rows ?? 3}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        placeholder={props.placeholder}
        className={`${inputClass(props.error)} resize-none`}
      />
    </FieldShell>
  )
}

export function CheckboxField({
  label,
  checked,
  onChange,
  hint,
}: {
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
  hint?: string
}) {
  const id = useId()
  return (
    <div className="flex items-start gap-3 sm:col-span-2">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 h-4 w-4 rounded border-gray-300 accent-emerald-800"
      />
      <label htmlFor={id} className="text-sm text-gray-700">
        {label}
        {hint && <span className="block text-xs text-gray-400">{hint}</span>}
      </label>
    </div>
  )
}

/** Grupo de campos con título, en una columna en celular y dos en pantallas anchas */
export function FormSection({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <fieldset className="flex flex-col gap-3">
      {title && (
        <legend className="mb-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">
          {title}
        </legend>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">{children}</div>
    </fieldset>
  )
}
