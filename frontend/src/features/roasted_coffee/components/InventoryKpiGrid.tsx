import { ArrowUpRight, CalendarClock, Hourglass, Package, PackageOpen, Wallet } from 'lucide-react'
import KpiCard from '../../../components/charts/KpiCard'
import { fmtCOP } from '../../../components/charts/chartData'
import { bags, fmtUnits, type InventoryKpis } from '../models/inventory'

export const KPI_GRID = 'grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6'

const days = (n: number) => `${fmtUnits(Math.round(n))} ${Math.round(n) === 1 ? 'día' : 'días'}`

export default function InventoryKpiGrid({ kpis }: { kpis: InventoryKpis }) {
  const variation =
    kpis.exitsPrev30 > 0 ? ((kpis.exits30 - kpis.exitsPrev30) / kpis.exitsPrev30) * 100 : null
  const outShare = kpis.totalIn > 0 ? Math.round((kpis.totalOut / kpis.totalIn) * 100) : 0

  return (
    <div className={KPI_GRID}>
      <KpiCard
        icon={<Package className="h-5 w-5" />}
        label="Disponible"
        value={bags(kpis.available)}
        sub={`${kpis.lots} ${kpis.lots === 1 ? 'lote' : 'lotes'} · ${kpis.products} ${kpis.products === 1 ? 'producto' : 'productos'}`}
        accent
      />
      <KpiCard
        icon={<Wallet className="h-5 w-5" />}
        label="Valor en bodega"
        value={fmtCOP(kpis.value)}
        sub={
          kpis.uncosted > 0
            ? `${kpis.uncosted} ${kpis.uncosted === 1 ? 'producto' : 'productos'} sin costo`
            : 'A costo de producción'
        }
      />
      <KpiCard
        icon={<ArrowUpRight className="h-5 w-5" />}
        label="Salidas · 30 días"
        value={bags(kpis.exits30)}
        sub={
          variation === null
            ? 'Sin salidas los 30 días anteriores'
            : `${variation >= 0 ? '+' : ''}${variation.toFixed(0)}% vs 30 días anteriores`
        }
      />
      <KpiCard
        icon={<Hourglass className="h-5 w-5" />}
        label="Cobertura"
        value={kpis.coverageDays === null ? '—' : `≈ ${days(kpis.coverageDays)}`}
        sub={
          kpis.coverageDays === null
            ? 'Sin salidas en 90 días'
            : `Al ritmo de ${fmtUnits(kpis.dailyRate)} bolsas/día (90 días)`
        }
      />
      <KpiCard
        icon={<CalendarClock className="h-5 w-5" />}
        label="Antigüedad promedio"
        value={kpis.avgAgeDays === null ? '—' : days(kpis.avgAgeDays)}
        sub={kpis.oldest ? `Más antiguo: lote #${kpis.oldest.lotId} (${days(kpis.oldest.days)})` : 'Sin existencias'}
      />
      <KpiCard
        icon={<PackageOpen className="h-5 w-5" />}
        label="Salidas históricas"
        value={bags(kpis.totalOut)}
        sub={`${outShare}% de lo que ha entrado`}
      />
    </div>
  )
}
