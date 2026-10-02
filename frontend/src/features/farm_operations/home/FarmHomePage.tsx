import type { LucideIcon } from 'lucide-react'
import { ClipboardList, HandCoins, MapPinned, Sprout, Sun } from 'lucide-react'

/**
 * Sección del módulo de cultivo que se mostrará en la entrada.
 */
interface FarmSection {
  icon: LucideIcon
  title: string
  description: string
}

const SECTIONS: FarmSection[] = [
  {
    icon: MapPinned,
    title: 'Fincas y lotes',
    description: 'Fincas, lotes, siembras y procedencia de la semilla.',
  },
  {
    icon: ClipboardList,
    title: 'Ciclos y labores',
    description: 'Fertilización, sanidad, floración, clima y demás labores de cada ciclo.',
  },
  {
    icon: HandCoins,
    title: 'Cosechas y jornales',
    description: 'Recolección diaria y pagos al peso o por jornal.',
  },
  {
    icon: Sun,
    title: 'Beneficio y secado',
    description: 'Del despulpado al pergamino seco que entra al inventario, con su calidad.',
  },
]

/**
 * Entrada del módulo de cultivo.
 *
 * Provisional: presenta las secciones del módulo mientras se construyen.
 * Las fincas la reemplazan como contenido principal y, más adelante, el
 * dashboard de cultivo.
 */
export default function FarmHomePage() {
  return (
    <div className="max-w-5xl text-left">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-800">
          <Sprout className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cultivo</h1>
          <p className="text-sm text-gray-500">
            Trazabilidad del café desde la finca hasta el pergamino seco.
          </p>
        </div>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {SECTIONS.map(({ icon: Icon, title, description }) => (
          <div
            key={title}
            className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <Icon className="h-5 w-5 text-emerald-700" />
              <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                Próximamente
              </span>
            </div>
            <h2 className="mt-3 font-semibold text-gray-900">{title}</h2>
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
