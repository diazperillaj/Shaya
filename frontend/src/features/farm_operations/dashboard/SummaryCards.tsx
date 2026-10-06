import { Award, BellRing, Cherry, Coffee, Coins, Factory, MapPinned, Percent, Sprout, Sun, Wallet, Warehouse } from 'lucide-react'
import KpiCard from '../../../components/charts/KpiCard'
import { fmtMoney, fmtNumber, plural } from '../format'
import type { DashboardSummary, FarmAlert } from '../models/types'

const KG_PER_ARROBA = 12.5

/** Tarjetas KPI: primero las de estado (el ahora), luego las del periodo (§3.1) */
export default function SummaryCards({ summary, alerts }: { summary: DashboardSummary; alerts: FarmAlert[] }) {
  const s = summary
  const count = (severity: FarmAlert['severity']) => alerts.filter((a) => a.severity === severity).length
  const delta = s.yield_pct !== null && s.yield_history_pct !== null ? s.yield_pct - s.yield_history_pct : null
  const area = s.area_by_variety.reduce((total, v) => total + v.area_ha, 0)
  const costPerKg = s.cherry_kg > 0 ? s.harvest_cost / s.cherry_kg : null

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Ahora</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-7">
        <KpiCard
          icon={<BellRing className="h-5 w-5" />}
          label="Alertas activas"
          value={String(alerts.length)}
          sub={`${count('high')} riesgos · ${count('medium')} desvíos · ${count('info')} recordatorios`}
          accent
        />
        <KpiCard
          icon={<MapPinned className="h-5 w-5" />}
          label="Fincas y lotes"
          value={`${s.farms_active} · ${s.plots_active}`}
          sub={`${fmtNumber(area, 1, 'ha')} sembradas`}
        />
        <KpiCard
          icon={<Sprout className="h-5 w-5" />}
          label="Ciclos activos"
          value={String(s.cycles_active)}
          sub={plural(s.harvests_open, 'cosecha abierta', 'cosechas abiertas')}
        />
        <KpiCard
          icon={<Wallet className="h-5 w-5" />}
          label="Pagos pendientes"
          value={fmtMoney(s.pending_payments)}
          sub="Recolección y jornales"
        />
        <KpiCard
          icon={<Factory className="h-5 w-5" />}
          label="En beneficio"
          value={fmtNumber(s.wet_in_progress.kg, 0, 'kg')}
          sub={
            s.wet_in_progress.count
              ? `${plural(s.wet_in_progress.count, 'beneficio', 'beneficios')} · el más antiguo, ${plural(s.wet_in_progress.oldest_days ?? 0, 'día', 'días')}`
              : 'Nada en beneficio'
          }
        />
        <KpiCard
          icon={<Sun className="h-5 w-5" />}
          label="En secado"
          value={fmtNumber(s.drying_in_progress.kg, 0, 'kg')}
          sub={
            s.drying_in_progress.count
              ? `${plural(s.drying_in_progress.count, 'secado', 'secados')} · el más antiguo, ${plural(s.drying_in_progress.oldest_days ?? 0, 'día', 'días')}`
              : 'Nada en secado'
          }
        />
        <KpiCard
          icon={<Warehouse className="h-5 w-5" />}
          label="Guardado en finca"
          value={fmtNumber(s.stored_parchment_kg, 0, 'kg')}
          sub="Pergamino seco por entrar al inventario"
        />
      </div>

      <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-gray-400">En el periodo</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
        <KpiCard
          icon={<Cherry className="h-5 w-5" />}
          label="Cereza cosechada"
          value={fmtNumber(s.cherry_kg, 0, 'kg')}
          sub={`${fmtNumber(s.cherry_kg / KG_PER_ARROBA, 0, '@')} · cosechas cerradas`}
        />
        <KpiCard
          icon={<Coffee className="h-5 w-5" />}
          label="Pergamino seco"
          value={fmtNumber(s.parchment_kg, 0, 'kg')}
          sub="Secados cerrados"
        />
        <KpiCard
          icon={<Percent className="h-5 w-5" />}
          label="Rendimiento"
          value={s.yield_pct === null ? '—' : `${fmtNumber(s.yield_pct, 1)} %`}
          sub={
            delta === null
              ? 'Pergamino seco / cereza trazada'
              : `${delta >= 0 ? '+' : ''}${fmtNumber(delta, 1)} pts frente al año anterior`
          }
        />
        <KpiCard
          icon={<Coins className="h-5 w-5" />}
          label="Costo de recolección"
          value={fmtMoney(s.harvest_cost)}
          sub={costPerKg === null ? 'Cosechas cerradas' : `${fmtMoney(costPerKg)} por kg de cereza`}
        />
        <KpiCard
          icon={<Award className="h-5 w-5" />}
          label="Puntaje promedio"
          value={s.score_avg === null ? '—' : fmtNumber(s.score_avg, 1)}
          sub={plural(s.evaluations, 'evaluación en pergamino', 'evaluaciones en pergamino')}
        />
      </div>
    </div>
  )
}
