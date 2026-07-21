import { Bot, Sparkles } from 'lucide-react'

interface Props {
  /** Módulo desde el que llegó el usuario (id de menuConfig) — personaliza las sugerencias. */
  previousMenuItem: number | null
  onPick: (question: string) => void
}

const GENERAL = [
  '¿Cómo va el negocio este mes?',
  '¿Cuál es el cliente que más ha comprado y qué productos?',
  '¿Cuánto café tostado queda en inventario?',
  '¿Cuánto hemos vendido este año?',
]

/** Sugerencias por módulo de origen (doc maestro §11: contextuales). */
const BY_MODULE: Record<number, string[]> = {
  0: GENERAL,
  1: [
    '¿Cuánto vendimos este mes?',
    'Top 5 productos más vendidos',
    '¿Qué llevaba la última venta?',
    '¿Cuál fue el mejor día de ventas?',
  ],
  11: [
    '¿Cuánto gastamos este mes y en qué categorías?',
    '¿Qué gastos pagamos con Nequi?',
    '¿Cuál es la categoría con más gasto este año?',
    '¿Cómo van los gastos mes a mes?',
  ],
  2: [
    '¿Cuánto café tostado queda por producto?',
    '¿Qué lotes están por agotarse?',
    '¿El lote 5 tuvo algún reempaque?',
    '¿Qué movimientos de maquilado hubo esta semana?',
  ],
  3: [
    '¿Cuántos kilos hemos procesado y con qué rendimiento?',
    '¿Qué variedad rinde mejor al tostar?',
    '¿Cuánto ha costado la maquila este año?',
    '¿Cómo fue el último proceso?',
  ],
  5: [
    '¿Quiénes son nuestros mejores clientes?',
    '¿Qué le gusta comprar a un cliente específico?',
    '¿Qué clientes compraron este mes?',
    '¿Cuál es el ticket promedio por cliente?',
  ],
  6: [
    '¿Qué producto se vende más?',
    '¿Cuánto queda de cada producto en inventario?',
    '¿Qué producto rota más rápido?',
    'Ventas por producto este año',
  ],
  7: [
    '¿Cuánto pergamino queda en inventario?',
    '¿A quién le compramos más café?',
    '¿A qué precio promedio compramos el kilo?',
    '¿Qué compras de pergamino hicimos este año?',
  ],
  8: [
    '¿A qué caficultor le compramos más?',
    '¿Qué variedades nos vende cada caficultor?',
    '¿Cuánto pagamos por kilo a cada caficultor?',
    '¿Cuándo fue la última compra de pergamino?',
  ],
  9: [
    '¿Qué movimientos de maquilado hubo este mes?',
    '¿Qué reempaques se han hecho?',
    '¿El lote 5 tuvo algún reempaque?',
    '¿Qué salidas de café hubo esta semana?',
  ],
}

/** Estado vacío: bienvenida + preguntas sugeridas según el módulo de origen. */
export default function SuggestionCards({ previousMenuItem, onPick }: Props) {
  const suggestions =
    (previousMenuItem !== null && BY_MODULE[previousMenuItem]) || GENERAL

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-8 overflow-y-auto">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-800 to-emerald-900 flex items-center justify-center shadow-lg mb-4">
        <Bot className="w-7 h-7 text-emerald-100" />
      </div>
      <h2 className="text-lg font-semibold text-gray-800">Asistente de Shaya</h2>
      <p className="text-sm text-gray-500 mt-1 mb-6 text-center max-w-sm">
        Pregunta sobre ventas, inventario, procesos, clientes o gastos. Las
        respuestas salen de los datos reales del negocio.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-xl">
        {suggestions.map((question) => (
          <button
            key={question}
            onClick={() => onPick(question)}
            className="group flex items-start gap-2 text-left bg-white border border-gray-100 hover:border-emerald-200 hover:bg-emerald-50/50 rounded-2xl px-4 py-3 text-sm text-gray-700 transition-all duration-200 shadow-sm hover:shadow"
          >
            <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600 group-hover:scale-110 transition-transform" />
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
