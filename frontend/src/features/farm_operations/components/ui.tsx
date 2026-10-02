import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'

/**
 * Piezas visuales del módulo de cultivo, con el estilo del resto de la app.
 */

const BUTTON_VARIANTS = {
  primary: 'bg-emerald-900 text-white shadow-md hover:bg-emerald-950',
  secondary: 'border border-gray-200 bg-white text-gray-700 shadow-sm hover:bg-gray-50',
  danger: 'border border-red-200 bg-white text-red-700 shadow-sm hover:bg-red-50',
}

export function Button({
  icon: Icon,
  variant = 'secondary',
  onClick,
  disabled,
  children,
}: {
  icon?: LucideIcon
  variant?: keyof typeof BUTTON_VARIANTS
  onClick: () => void
  disabled?: boolean
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition disabled:opacity-50 ${BUTTON_VARIANTS[variant]}`}
    >
      {Icon && <Icon className="h-4 w-4" />}
      {children}
    </button>
  )
}

const BADGE_TONES = {
  green: 'bg-emerald-100 text-emerald-800',
  gray: 'bg-gray-100 text-gray-600',
  amber: 'bg-amber-100 text-amber-800',
  blue: 'bg-sky-100 text-sky-800',
}

export function Badge({ tone = 'gray', children }: { tone?: keyof typeof BADGE_TONES; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE_TONES[tone]}`}>
      {children}
    </span>
  )
}

export function PageHeader({
  icon: Icon,
  title,
  subtitle,
  back,
  actions,
}: {
  icon: LucideIcon
  title: ReactNode
  subtitle?: ReactNode
  /** Enlace para volver a la página anterior del módulo */
  back?: { to: string; label: string }
  actions?: ReactNode
}) {
  return (
    <div className="flex flex-col gap-3">
      {back && (
        <Link to={back.to} className="flex w-fit items-center gap-1.5 text-sm text-gray-500 hover:text-emerald-800">
          <ArrowLeft className="h-4 w-4" /> {back.label}
        </Link>
      )}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="rounded-xl bg-emerald-100 p-2.5">
            <Icon className="h-6 w-6 text-emerald-800" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {subtitle && <div className="mt-0.5 text-sm text-gray-500">{subtitle}</div>}
          </div>
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  )
}

export function Card({
  title,
  actions,
  children,
}: {
  title?: string
  actions?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
      {(title || actions) && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="font-semibold text-gray-900">{title}</h2>}
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}

/** Lista de pares etiqueta / valor */
export function DetailList({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt className="text-xs text-gray-400">{label}</dt>
          <dd className="text-sm text-gray-900">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-10 text-center">
      <Icon className="h-8 w-8 text-gray-300" />
      <div>
        <p className="font-medium text-gray-700">{title}</p>
        {description && <p className="mt-1 text-sm text-gray-400">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export function Loading() {
  return (
    <div className="flex justify-center py-12">
      <Loader2 className="h-6 w-6 animate-spin text-emerald-800" />
    </div>
  )
}

export function ErrorMessage({ message }: { message: string }) {
  return (
    <p className="whitespace-pre-line rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </p>
  )
}
