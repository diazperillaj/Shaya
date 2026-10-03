import { useCallback, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, Undo2, Wallet } from 'lucide-react'
import { inputClass } from '../components/styles'
import { EmptyState, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { fmtDate, fmtMoney, plural, todayIso } from '../format'
import type { PaymentItem } from '../models/types'
import { fetchFarm } from '../services/farms.api'
import { fetchPaymentItems, payItems, unpayItems } from '../services/payroll.api'
import { describePaymentItem } from './describe'

type Tab = 'pending' | 'paid'
const itemKey = (item: PaymentItem) => `${item.kind}-${item.id}`

/**
 * Pagos de la finca: la recolección y los jornales pendientes, por
 * empleado. Se elige qué pagar y se paga en una sola operación; en
 * «Pagados» se puede deshacer un pago marcado por error.
 */
export default function PaymentsPage() {
  const { farmId } = useParams()
  return <Payments key={farmId} farmId={Number(farmId)} />
}

function Payments({ farmId }: { farmId: number }) {
  const [tab, setTab] = useState<Tab>('pending')
  const loadFarm = useCallback(() => fetchFarm(farmId), [farmId])
  const { data: farm } = useLoader(loadFarm)

  return (
    <div className="flex flex-col gap-6 pb-24">
      <PageHeader
        icon={Wallet}
        back={{ to: `/cultivo/fincas/${farmId}`, label: farm?.name ?? 'Finca' }}
        title="Pagos"
        subtitle="Recolección y jornales de los trabajadores de la finca."
      />
      <div className="flex gap-1 rounded-xl bg-gray-100 p-1 sm:w-fit" role="tablist">
        {(['pending', 'paid'] as Tab[]).map((option) => (
          <button
            key={option}
            type="button"
            role="tab"
            aria-selected={tab === option}
            onClick={() => setTab(option)}
            className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition ${
              tab === option ? 'bg-white text-emerald-900 shadow-sm' : 'text-gray-500'
            }`}
          >
            {option === 'pending' ? 'Pendientes' : 'Pagados'}
          </button>
        ))}
      </div>
      {/* Cada pestaña con su propia selección */}
      <PaymentList key={tab} farmId={farmId} paid={tab === 'paid'} />
    </div>
  )
}

function PaymentList({ farmId, paid }: { farmId: number; paid: boolean }) {
  const load = useCallback(() => fetchPaymentItems(farmId, paid), [farmId, paid])
  const { data: items, error, reload } = useLoader(load)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [paidAt, setPaidAt] = useState(todayIso())
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const byEmployee = useMemo(() => {
    const groups = new Map<number, { name: string; items: PaymentItem[] }>()
    for (const item of items ?? []) {
      const group = groups.get(item.employee_id) ?? { name: item.employee_name, items: [] }
      group.items.push(item)
      groups.set(item.employee_id, group)
    }
    return [...groups.values()]
  }, [items])

  const chosen = (items ?? []).filter((item) => selected.has(itemKey(item)))
  const chosenTotal = chosen.reduce((sum, item) => sum + item.amount, 0)

  const toggle = (keys: string[], on: boolean) =>
    setSelected((current) => {
      const next = new Set(current)
      keys.forEach((key) => (on ? next.add(key) : next.delete(key)))
      return next
    })

  const submit = async () => {
    const selection = {
      harvest_work_ids: chosen.filter((item) => item.kind === 'harvest_work').map((item) => item.id),
      day_labor_ids: chosen.filter((item) => item.kind === 'day_labor').map((item) => item.id),
    }
    setBusy(true)
    setActionError(null)
    try {
      const result = paid ? await unpayItems(selection) : await payItems(selection, paidAt)
      setMessage(
        `${paid ? 'Pago deshecho' : 'Pagado'}: ${plural(result.count, 'registro', 'registros')} por ${fmtMoney(result.total)}`,
      )
      setSelected(new Set())
      reload()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Error registrando el pago')
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorMessage message={error} />
  if (!items) return <Loading />

  return (
    <div className="flex flex-col gap-4">
      {message && <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{message}</p>}
      {items.length === 0 && (
        <EmptyState
          icon={Wallet}
          title={paid ? 'Aún no hay pagos registrados' : 'No hay nada pendiente de pago'}
          description={paid ? undefined : 'La recolección y los jornales sin pagar aparecen aquí, por trabajador.'}
        />
      )}

      {byEmployee.map((group) => {
        const keys = group.items.map(itemKey)
        const allOn = keys.every((key) => selected.has(key))
        const total = group.items.reduce((sum, item) => sum + item.amount, 0)
        return (
          <section key={group.name} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
            <label className="mb-2 flex cursor-pointer items-center justify-between gap-3">
              <span className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={allOn}
                  onChange={() => toggle(keys, !allOn)}
                  className="h-4 w-4 rounded border-gray-300 accent-emerald-800"
                />
                <span className="font-medium text-gray-900">{group.name}</span>
              </span>
              <span className="text-sm font-semibold text-gray-900">{fmtMoney(total)}</span>
            </label>
            <ul className="divide-y divide-gray-100">
              {group.items.map((item) => (
                <li key={itemKey(item)}>
                  <label className="flex cursor-pointer items-center justify-between gap-3 py-2 pl-7">
                    <span className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={selected.has(itemKey(item))}
                        onChange={(e) => toggle([itemKey(item)], e.target.checked)}
                        aria-label={describePaymentItem(item)}
                        className="mt-0.5 h-4 w-4 rounded border-gray-300 accent-emerald-800"
                      />
                      <span>
                        <span className="block text-sm text-gray-900">{describePaymentItem(item)}</span>
                        <span className="block text-xs text-gray-400">
                          {fmtDate(item.item_date)}
                          {item.paid_at && ` · pagado el ${fmtDate(item.paid_at)}`}
                        </span>
                      </span>
                    </span>
                    <span className="whitespace-nowrap text-sm text-gray-900">{fmtMoney(item.amount)}</span>
                  </label>
                </li>
              ))}
            </ul>
          </section>
        )
      })}

      {chosen.length > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
          {/* Controles a la derecha: abajo a la izquierda está el botón del menú lateral */}
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-end gap-2">
            <p className="w-full text-sm text-gray-700 sm:mr-auto sm:w-auto">
              {plural(chosen.length, 'registro', 'registros')} · <span className="font-semibold">{fmtMoney(chosenTotal)}</span>
            </p>
            <div className="flex items-center gap-2">
              {!paid && (
                <div className="w-40">
                  <input
                    type="date"
                    aria-label="Fecha de pago"
                    value={paidAt}
                    max={todayIso()}
                    onChange={(e) => setPaidAt(e.target.value)}
                    className={`${inputClass()} py-2`}
                  />
                </div>
              )}
              <button
                type="button"
                onClick={submit}
                disabled={busy || (!paid && !paidAt)}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium shadow-md transition disabled:opacity-60 ${
                  paid ? 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50' : 'bg-emerald-900 text-white hover:bg-emerald-950'
                }`}
              >
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : paid ? <Undo2 className="h-4 w-4" /> : <Wallet className="h-4 w-4" />}
                {paid ? 'Deshacer pago' : 'Pagar'}
              </button>
            </div>
          </div>
          {actionError && <p className="mx-auto mt-2 max-w-6xl text-sm text-red-700">{actionError}</p>}
        </div>
      )}
    </div>
  )
}
