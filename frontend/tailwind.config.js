/** @type {import('tailwindcss').Config} */
import plugin from 'tailwindcss/plugin'
import { themeColors, themeVariables } from './tailwind.theme.js'

export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    // Cada papel lee su variable: el modo oscuro cambia fondos, textos y bordes por separado
    colors: themeColors.base,
    backgroundColor: themeColors.bg,
    gradientColorStops: themeColors.bg,
    textColor: themeColors.text,
    placeholderColor: themeColors.text,
    borderColor: themeColors.border,
    ringColor: { ...themeColors.border, DEFAULT: 'rgb(var(--border-emerald-600) / 0.5)' },
    outlineColor: themeColors.border,
    extend: {
      fontFamily: {
        sans: ['Roboto', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      },
      transitionTimingFunction: {
        // Salida rápida: la respuesta se ve de inmediato
        out: 'cubic-bezier(0.23, 1, 0.32, 1)',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(8px) scale(0.98)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 150ms cubic-bezier(0.23, 1, 0.32, 1)',
        slideUp: 'slideUp 220ms cubic-bezier(0.23, 1, 0.32, 1)',
      },
    },
  },
  plugins: [
    plugin(({ addBase }) => {
      addBase({
        ':root': themeVariables.light,
        '.dark': themeVariables.dark,
      })
    }),
  ],
}
