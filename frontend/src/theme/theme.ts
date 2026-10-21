import { useSyncExternalStore } from 'react'

/**
 * Modo claro u oscuro.
 *
 * Por defecto, claro. Cuando el usuario elige con el botón, su elección se
 * recuerda en este navegador. El script de `index.html` aplica la elección
 * guardada antes de pintar, para que la página no parpadee al cargar.
 */
export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'shaya-theme'

function current(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

function apply(theme: Theme): void {
  const root = document.documentElement
  // Sin transiciones durante el cambio: todo cambia a la vez
  root.classList.add('theme-switching')
  root.classList.toggle('dark', theme === 'dark')
  root.style.colorScheme = theme
  void window.getComputedStyle(root).opacity // fuerza el estilo antes de volver a habilitar transiciones
  requestAnimationFrame(() => root.classList.remove('theme-switching'))
  listeners.forEach((listener) => listener())
}

const listeners = new Set<() => void>()

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Sin almacenamiento (modo privado): el cambio vale para esta visita
  }
  apply(theme)
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, current, () => 'light' as Theme)
  return { theme, toggle: () => setTheme(theme === 'dark' ? 'light' : 'dark') }
}
