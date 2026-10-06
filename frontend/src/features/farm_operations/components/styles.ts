/** Clases de un control de formulario, con borde rojo si tiene error */
export const inputClass = (error?: string) =>
  `w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 transition-[border-color,box-shadow] duration-150 focus:border-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-600/25 ${
    error ? 'border-red-400' : 'border-gray-200'
  }`
