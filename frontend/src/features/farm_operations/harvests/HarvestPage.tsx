import { useCallback, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Apple, CircleCheck, Loader2, Pencil, Plus, RotateCcw, Wallet } from 'lucide-react'
import { FormSection } from '../components/fields'
import { Badge, Button, Card, ErrorMessage, Loading, PageHeader } from '../components/ui'
import { useFormValues } from '../components/useFormValues'
import { useLoader } from '../components/useLoader'
import { fromKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { fmtDate, fmtMoney, fmtNumber, todayIso } from '../format'
import type { HarvestDetail, HarvestWork } from '../models/types'
import { fetchEmployees } from '../services/employees.api'
import { createHarvestWork, fetchHarvest } from '../services/harvests.api'
import QualityCard from '../quality/QualityCard'
import HarvestFormDialog from './HarvestFormDialog'
import HarvestStatusDialog from './HarvestStatusDialog'
import HarvestWorkDialog from './HarvestWorkDialog'
import WorkFields from './WorkFields'
import type { EmployeeOption } from './WorkFields'
import { emptyWork, workErrors, workPayload } from './workForm'
import type { WorkValues } from './workForm'

/**
 * Una pasada de cosecha, como sesión de trabajo (patrón de las ferias):
 * registro rápido de la recolección de cada día, acumulado en vivo y
 * resumen por recolector para liquidar los pagos.
 */
export default function HarvestPage() {
  const { harvestId } = useParams()
  return <HarvestView key={harvestId} id={Number(harvestId)} />
}

type Dialog = { kind: 'edit' | 'status' } | { kind: 'work'; work: HarvestWork } | null

function HarvestView({ id }: { id: number }) {
  const navigate = useNavigate()
  const load = useCallback(() => fetchHarvest(id), [id])
  const { data: harvest, error, reload } = useLoader(load)
  const [dialog, setDialog] = useState<Dialog>(null)

  if (error) {
    return (
      <div className="flex flex-col gap-4">
        <Link to="/cultivo/fincas" className="text-sm text-emerald-800 hover:underline">← Volver a las fincas</Link>
        <ErrorMessage message={error} />
      </div>
    )
  }
  if (!harvest) return <Loading />

  const open = harvest.status === 'open'
  const closeAndReload = () => {
    setDialog(null)
    reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        icon={Apple}
        back={{ to: `/cultivo/lotes/${harvest.plot_id}`, label: harvest.plot_name }}
        title={
          <span className="flex flex-wrap items-center gap-2">
            Pasada {harvest.pass_number}
            <Badge tone={open ? 'green' : 'gray'}>{open ? 'Abierta' : 'Cerrada'}</Badge>
          </span>
        }
        subtitle={`Lote «${harvest.plot_name}» · ciclo ${harvest.cycle_number} · ${
          open ? `desde el ${fmtDate(harvest.start_date)}` : `del ${fmtDate(harvest.start_date)} al ${fmtDate(harvest.end_date)}`
        }`}
        actions={
          <>
            <Button icon={Wallet} onClick={() => navigate(`/cultivo/fincas/${harvest.farm_id}/pagos`)}>Pagos</Button>
            <Button icon={Pencil} onClick={() => setDialog({ kind: 'edit' })}>Editar</Button>
            {open ? (
              <Button variant="primary" icon={CircleCheck} onClick={() => setDialog({ kind: 'status' })}>
                Cerrar cosecha
              </Button>
            ) : (
              <Button icon={RotateCcw} onClick={() => setDialog({ kind: 'status' })}>Reabrir</Button>
            )}
          </>
        }
      />

      <Totals harvest={harvest} />
      {open && <WorkEntry harvest={harvest} onAdded={reload} />}
      <WorksByDay harvest={harvest} onEdit={(work) => setDialog({ kind: 'work', work })} />
      <WorksByEmployee harvest={harvest} />
      <QualityCard stage="cherry" target={{ harvest_id: harvest.id }} />

      {dialog?.kind === 'edit' && (
        <HarvestFormDialog
          cycle={{ id: harvest.crop_cycle_id, cycle_number: harvest.cycle_number }}
          plotName={harvest.plot_name}
          harvest={harvest}
          onClose={() => setDialog(null)}
          onSaved={(savedId) => (savedId === null ? navigate(`/cultivo/lotes/${harvest.plot_id}`) : closeAndReload())}
        />
      )}
      {dialog?.kind === 'status' && (
        <HarvestStatusDialog harvest={harvest} onClose={() => setDialog(null)} onSaved={closeAndReload} />
      )}
      {dialog?.kind === 'work' && (
        <WorkCorrection harvest={harvest} work={dialog.work} onClose={() => setDialog(null)} onSaved={closeAndReload} />
      )}
    </div>
  )
}

/** Acumulados de la pasada */
function Totals({ harvest }: { harvest: HarvestDetail }) {
  const today = todayIso()
  const kgToday = harvest.works
    .filter((work) => work.work_date === today)
    .reduce((sum, work) => sum + (work.kg_collected ?? 0), 0)
  const pickers = new Set(harvest.works.map((work) => work.employee_id)).size

  const tiles: [string, string, string?][] = [
    ['Café registrado', fmtNumber(harvest.kg_registered, 1, 'kg'), `${fmtNumber(fromKg(harvest.kg_registered, 'arroba'), 1, '@')} · ${pickers} recolectores`],
    harvest.status === 'closed'
      ? ['Total de cereza', fmtNumber(harvest.total_cherry_kg, 1, 'kg'), 'Al cerrar la pasada']
      : ['Recogido hoy', fmtNumber(kgToday, 1, 'kg'), fmtDate(today)],
    ['Valor de la recolección', fmtMoney(harvest.value_total), `${harvest.works_count} registros`],
    ['Pendiente de pago', fmtMoney(harvest.value_pending), harvest.value_pending > 0 ? 'Por liquidar' : 'Todo pagado'],
    ['Beneficiado', fmtNumber(harvest.kg_processed, 1, 'kg'), 'Café cereza ya en beneficio'],
  ]

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
      {tiles.map(([label, value, detail]) => (
        <div key={label} className="rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
          <p className="text-xs text-gray-500">{label}</p>
          <p className="mt-1 text-xl font-semibold text-gray-900">{value}</p>
          {detail && <p className="text-xs text-gray-400">{detail}</p>}
        </div>
      ))}
    </div>
  )
}

/**
 * Registro rápido de la recolección: tras agregar, conserva la fecha, la
 * forma de pago y la unidad, y limpia el resto para el siguiente recolector.
 */
function WorkEntry({ harvest, onAdded }: { harvest: HarvestDetail; onAdded: () => void }) {
  const loadEmployees = useCallback(() => fetchEmployees(harvest.farm_id), [harvest.farm_id])
  const { data: employees, reload: reloadEmployees } = useLoader(loadEmployees)
  const [formKey, setFormKey] = useState(0)
  const [kept, setKept] = useState<{ values: WorkValues; unit: WeightUnit }>({ values: emptyWork(), unit: 'kg' })
  const [last, setLast] = useState<string | null>(null)

  const active = (employees ?? []).filter((employee) => employee.active)

  return (
    <Card title="Registrar recolección">
      <EntryForm
        key={formKey}
        harvest={harvest}
        employees={active}
        initial={kept}
        onEmployeeCreated={reloadEmployees}
        onAdded={(work, values, unit) => {
          setKept({ values: { ...emptyWork(), work_date: values.work_date, payment_type: values.payment_type }, unit })
          setFormKey((key) => key + 1)
          setLast(
            `${work.employee_name}: ${work.kg_collected !== null ? `${fmtNumber(work.kg_collected, 3, 'kg')} · ` : ''}${fmtMoney(work.total_value)}`,
          )
          onAdded()
        }}
      />
      {last && <p className="mt-3 text-sm text-emerald-800">Agregado — {last}</p>}
    </Card>
  )
}

function EntryForm({
  harvest,
  employees,
  initial,
  onEmployeeCreated,
  onAdded,
}: {
  harvest: HarvestDetail
  employees: EmployeeOption[]
  initial: { values: WorkValues; unit: WeightUnit }
  onEmployeeCreated: () => void
  onAdded: (work: HarvestWork, values: WorkValues, unit: WeightUnit) => void
}) {
  const { values, bind, setFieldError } = useFormValues<keyof WorkValues>(initial.values)
  const [unit, setUnit] = useState<WeightUnit>(initial.unit)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const errors = workErrors(values, harvest)
    errors.forEach(([field, message]) => setFieldError(field, message))
    if (errors.length > 0) return
    setBusy(true)
    setError(null)
    try {
      onAdded(await createHarvestWork(harvest.id, workPayload(values, unit)), values, unit)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error registrando la recolección')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <FormSection>
        <WorkFields
          harvest={harvest}
          employees={employees}
          values={values}
          bind={bind}
          unit={unit}
          onUnitChange={setUnit}
          onEmployeeCreated={(employee) => {
            onEmployeeCreated()
            bind('employee_id').onChange(String(employee.id))
          }}
        />
      </FormSection>
      {error && <ErrorMessage message={error} />}
      <button
        type="submit"
        disabled={busy}
        className="flex items-center justify-center gap-2 self-end rounded-xl bg-emerald-900 px-5 py-2.5 text-sm font-medium text-white shadow-md transition hover:bg-emerald-950 disabled:opacity-60"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
        Agregar
      </button>
    </form>
  )
}

/** Recolección agrupada por día, con el acumulado de cada día */
function WorksByDay({ harvest, onEdit }: { harvest: HarvestDetail; onEdit: (work: HarvestWork) => void }) {
  const days = useMemo(() => {
    const groups = new Map<string, HarvestWork[]>()
    harvest.works.forEach((work) => groups.set(work.work_date, [...(groups.get(work.work_date) ?? []), work]))
    return [...groups.entries()]
  }, [harvest.works])
  const editable = harvest.status === 'open'

  return (
    <Card title="Recolección">
      {days.length === 0 && (
        <p className="text-sm text-gray-400">Aún no hay recolección registrada en esta pasada.</p>
      )}
      <div className="flex flex-col gap-4">
        {days.map(([day, works]) => {
          const kg = works.reduce((sum, work) => sum + (work.kg_collected ?? 0), 0)
          const value = works.reduce((sum, work) => sum + work.total_value, 0)
          return (
            <section key={day}>
              <p className="mb-1 flex flex-wrap justify-between gap-2 text-xs font-medium text-gray-500">
                <span>{fmtDate(day)}</span>
                <span>{fmtNumber(kg, 1, 'kg')} · {fmtMoney(value)}</span>
              </p>
              <ul className="divide-y divide-gray-100 rounded-xl border border-gray-100">
                {works.map((work) => {
                  const canEdit = editable && !work.paid
                  return (
                    <li key={work.id}>
                      <button
                        type="button"
                        disabled={!canEdit}
                        onClick={() => onEdit(work)}
                        className="flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left enabled:hover:bg-gray-50"
                      >
                        <span>
                          <span className="block text-sm text-gray-900">{work.employee_name}</span>
                          <span className="block text-xs text-gray-500">{describeWork(work)}</span>
                        </span>
                        <span className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900">{fmtMoney(work.total_value)}</span>
                          <Badge tone={work.paid ? 'green' : 'amber'}>{work.paid ? 'Pagado' : 'Pendiente'}</Badge>
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </section>
          )
        })}
      </div>
      {!editable && harvest.works.length > 0 && (
        <p className="mt-3 text-xs text-gray-400">La pasada está cerrada: reábrela para corregir su recolección.</p>
      )}
    </Card>
  )
}

const describeWork = (work: HarvestWork): string =>
  work.payment_type === 'per_kg'
    ? `${fmtNumber(work.kg_collected, 3, 'kg')} × ${fmtMoney(work.rate_per_kg)}/kg`
    : `Jornal${work.kg_collected !== null ? ` · ${fmtNumber(work.kg_collected, 3, 'kg')}` : ''}`

/** Resumen por recolector: lo recogido, lo ganado y lo pendiente */
function WorksByEmployee({ harvest }: { harvest: HarvestDetail }) {
  const rows = useMemo(() => {
    const byEmployee = new Map<number, { name: string; kg: number; value: number; pending: number }>()
    harvest.works.forEach((work) => {
      const row = byEmployee.get(work.employee_id) ?? { name: work.employee_name, kg: 0, value: 0, pending: 0 }
      row.kg += work.kg_collected ?? 0
      row.value += work.total_value
      if (!work.paid) row.pending += work.total_value
      byEmployee.set(work.employee_id, row)
    })
    return [...byEmployee.values()].sort((a, b) => b.kg - a.kg)
  }, [harvest.works])

  if (rows.length === 0) return null
  return (
    <Card title="Por recolector">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-gray-500">
            <tr>
              <th className="py-2 pr-3 font-medium">Recolector</th>
              <th className="py-2 pr-3 text-right font-medium">Café</th>
              <th className="py-2 pr-3 text-right font-medium">Valor</th>
              <th className="py-2 text-right font-medium">Pendiente</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rows.map((row) => (
              <tr key={row.name}>
                <td className="py-2 pr-3 text-gray-900">{row.name}</td>
                <td className="py-2 pr-3 text-right">{fmtNumber(row.kg, 1, 'kg')}</td>
                <td className="py-2 pr-3 text-right">{fmtMoney(row.value)}</td>
                <td className="py-2 text-right">{fmtMoney(row.pending)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

/** Diálogo de corrección con los empleados activos de la finca (y el del registro) */
function WorkCorrection({
  harvest,
  work,
  onClose,
  onSaved,
}: {
  harvest: HarvestDetail
  work: HarvestWork
  onClose: () => void
  onSaved: () => void
}) {
  const loadEmployees = useCallback(() => fetchEmployees(harvest.farm_id), [harvest.farm_id])
  const { data: employees } = useLoader(loadEmployees)
  if (!employees) return null

  const options: EmployeeOption[] = employees.filter((employee) => employee.active)
  if (!options.some((employee) => employee.id === work.employee_id)) {
    options.push({ id: work.employee_id, full_name: work.employee_name })
  }
  return <HarvestWorkDialog harvest={harvest} work={work} employees={options} onClose={onClose} onSaved={onSaved} />
}
