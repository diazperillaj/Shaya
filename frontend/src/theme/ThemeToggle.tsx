import { Moon, Sun } from 'lucide-react'
import { useTheme } from './theme'

/**
 * Interruptor de modo claro / oscuro.
 *
 * - `sidebar`: fila del pie del menú lateral (con el texto si está abierto).
 * - `floating`: botón redondo para pantallas sin menú (inicio de sesión).
 */
export default function ThemeToggle({
  variant = 'sidebar',
  showLabel = true,
}: {
  variant?: 'sidebar' | 'floating'
  showLabel?: boolean
}) {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  const label = dark ? 'Modo claro' : 'Modo oscuro'

  const icon = (
    <span className="relative h-5 w-5 flex-shrink-0" aria-hidden>
      <Sun
        className={`absolute inset-0 h-5 w-5 transition-[opacity,transform] duration-200 ease-out ${
          dark ? 'rotate-0 scale-100 opacity-100' : '-rotate-90 scale-50 opacity-0'
        }`}
      />
      <Moon
        className={`absolute inset-0 h-5 w-5 transition-[opacity,transform] duration-200 ease-out ${
          dark ? 'rotate-90 scale-50 opacity-0' : 'rotate-0 scale-100 opacity-100'
        }`}
      />
    </span>
  )

  if (variant === 'floating') {
    return (
      <button
        type="button"
        onClick={toggle}
        aria-label={label}
        title={label}
        className="flex h-11 w-11 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600 shadow-sm transition-[transform,background-color] duration-150 ease-out hover:bg-gray-50 active:scale-[0.96]"
      >
        {icon}
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={showLabel ? undefined : label}
      title={showLabel ? undefined : label}
      className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-emerald-100 transition-[transform,background-color,color] duration-150 ease-out hover:bg-white/10 hover:text-white active:scale-[0.98] ${
        showLabel ? '' : 'justify-center'
      }`}
    >
      {icon}
      {showLabel && <span>{label}</span>}
    </button>
  )
}
