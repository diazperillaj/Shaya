/**
 * Paleta con modo claro y oscuro.
 *
 * Los componentes siguen usando las clases de siempre (`bg-white`,
 * `text-gray-700`, `border-emerald-200`…). Cada utilidad lee una variable CSS
 * según su papel —fondo, texto o borde— y el modo oscuro solo cambia las
 * variables. Así un mismo tono puede ser fondo claro en un modo y fondo
 * oscuro en el otro sin tocar el código de cada pantalla.
 *
 * Modo claro: los colores por defecto de Tailwind (el diseño de siempre).
 * Modo oscuro: gris carbón con un toque verde; el esmeralda sigue siendo el
 * color de marca y de acento.
 */
import colors from 'tailwindcss/colors'

const SHADES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
/** Familias con modo oscuro; el resto de la paleta queda igual en ambos modos */
const THEMED = ['emerald', 'red', 'amber', 'sky', 'yellow', 'orange']
const ROLES = ['bg', 'text', 'border']

/** Superficies del modo oscuro */
export const DARK_SURFACE = {
  page: '#0f1412',   // fondo de la página
  surface: '#161c19', // tarjetas, tablas, diálogos (bg-white)
  sidebar: '#0c2a21', // menú lateral
}

/** Grises del modo oscuro por papel: fondos que suben, textos que se aclaran */
const GRAY_DARK = {
  bg: {
    50: '#1b221f', 100: '#212925', 200: '#29322e', 300: '#343e39', 400: '#4b5651', 500: '#66716b',
    600: '#7d8882', 700: '#3a4440', 800: '#2e3733', 900: '#252d29', 950: '#1d2421',
  },
  text: {
    50: '#1f2622', 100: '#2c3430', 200: '#3f4844', 300: '#5d6762', 400: '#848f89', 500: '#99a49e',
    600: '#b0bab4', 700: '#c6cec9', 800: '#d8dfdb', 900: '#e9edeb', 950: '#f3f5f4',
  },
  border: {
    50: '#1b221f', 100: '#232b27', 200: '#2c3531', 300: '#3a443f', 400: '#4d5853', 500: '#67726c',
    600: '#7e8983', 700: '#96a09b', 800: '#b2bab6', 900: '#ced4d1', 950: '#e3e7e5',
  },
}

const rgb = (hex) => {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}
const triplet = (hex) => rgb(hex).join(' ')
const mix = (base, over, amount) =>
  '#' + rgb(base)
    .map((c, i) => Math.round(c + (rgb(over)[i] - c) * amount))
    .map((c) => c.toString(16).padStart(2, '0'))
    .join('')

/** Tono oscuro de un color de la paleta según su papel */
function darkShade(family, shade, role) {
  const scale = colors[family]
  if (role === 'text') {
    // Los textos oscuros (sobre fondos claros) se aclaran; los claros ya sirven sobre fondo oscuro
    const lighter = { 600: 400, 700: 300, 800: 300, 900: 200, 950: 100 }[shade]
    return lighter ? scale[lighter] : scale[shade]
  }
  // Fondos y bordes muy claros se vuelven tintes sobre la superficie oscura
  const tint = role === 'bg'
    ? { 50: 0.14, 100: 0.22, 200: 0.32, 300: 0.45 }[shade]
    : { 50: 0.18, 100: 0.26, 200: 0.36, 300: 0.5 }[shade]
  return tint ? mix(DARK_SURFACE.surface, scale[role === 'bg' ? 600 : 500], tint) : scale[shade]
}

/** Valores de cada variable: `{ light: {--x: 'r g b'}, dark: {...} }` */
function variables() {
  const light = {}
  const dark = {}
  for (const role of ROLES) {
    for (const shade of SHADES) {
      light[`--${role}-gray-${shade}`] = triplet(colors.gray[shade])
      dark[`--${role}-gray-${shade}`] = triplet(GRAY_DARK[role][shade])
      for (const family of THEMED) {
        light[`--${role}-${family}-${shade}`] = triplet(colors[family][shade])
        dark[`--${role}-${family}-${shade}`] = triplet(darkShade(family, shade, role))
      }
    }
  }
  const surfaces = {
    '--bg-white': ['#ffffff', DARK_SURFACE.surface],
    '--text-white': ['#ffffff', '#ffffff'],
    '--border-white': ['#ffffff', '#ffffff'],
    '--bg-black': ['#000000', '#000000'],
    '--text-black': ['#000000', GRAY_DARK.text[900]],
    '--border-black': ['#000000', GRAY_DARK.border[900]],
    '--page': [colors.gray[50], DARK_SURFACE.page],
  }
  for (const [name, [l, d]] of Object.entries(surfaces)) {
    light[name] = triplet(l)
    dark[name] = triplet(d)
  }
  return { light, dark }
}

const ref = (name) => `rgb(var(${name}) / <alpha-value>)`

/** Paleta de un papel: las familias con modo oscuro leen su variable */
function palette(role) {
  const result = { white: ref(`--${role}-white`), black: ref(`--${role}-black`) }
  for (const family of ['gray', ...THEMED]) {
    result[family] = Object.fromEntries(SHADES.map((s) => [s, ref(`--${role}-${family}-${s}`)]))
  }
  return result
}

/** El resto de la paleta de Tailwind, igual en ambos modos (sin los nombres en desuso) */
const DEPRECATED = ['lightBlue', 'warmGray', 'trueGray', 'coolGray', 'blueGray']
const staticColors = Object.fromEntries(
  Object.entries(Object.getOwnPropertyDescriptors(colors))
    .filter(([name, d]) => !DEPRECATED.includes(name) && 'value' in d)
    .map(([name, d]) => [name, d.value]),
)

/**
 * `bg-white` es la superficie (tarjetas, tablas) y cambia con el tema; pero
 * `bg-white/10` y otras transparencias bajas son velos de luz sobre fondos
 * de color (menú, encabezados verdes) y siguen siendo blancos en ambos modos.
 */
const surfaceWhite = ({ opacityValue }) => {
  const alpha = Number(opacityValue)
  if (opacityValue !== undefined && !Number.isNaN(alpha) && alpha < 0.5) {
    return `rgb(255 255 255 / ${opacityValue})`
  }
  return opacityValue === undefined ? 'rgb(var(--bg-white))' : `rgb(var(--bg-white) / ${opacityValue})`
}

export const themeColors = {
  base: { ...staticColors, ...palette('text') },
  bg: { ...staticColors, ...palette('bg'), white: surfaceWhite },
  text: { ...staticColors, ...palette('text') },
  border: { ...staticColors, ...palette('border'), DEFAULT: ref('--border-gray-200') },
}

export const themeVariables = variables()
