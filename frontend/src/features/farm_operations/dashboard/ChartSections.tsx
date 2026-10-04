import ChartCard from '../../../components/charts/ChartCard'
import DonutChart from '../../../components/charts/DonutChart'
import { toRecharts } from '../../../components/charts/chartData'
import { fmtNumber } from '../format'
import type { ProductionCharts, QualityCharts } from '../models/types'
import { asCop, asCount, asKg, asPct, asScore, humidityBinInside, unitName } from './chartFormat'
import FarmChart, { NoData } from './FarmChart'

/** Gráficas de producción (§3.2) */
export function ProductionSection({ charts }: { charts: ProductionCharts }) {
  const unit = charts.unit
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <div className="xl:col-span-2">
        <ChartCard title="Producción mensual" subtitle="Cereza de las cosechas cerradas y pergamino seco de los secados cerrados">
          <FarmChart chart={charts.monthly} format={asKg} />
        </ChartCard>
      </div>
      <ChartCard title={`Pergamino por ${unitName(unit)}`} subtitle="Pergamino seco repartido según la cereza que aportó cada origen">
        <FarmChart chart={charts.by_unit} format={asKg} horizontal />
      </ChartCard>
      <ChartCard
        title={`Rendimiento por ${unitName(unit)}`}
        subtitle={
          charts.yield_reference_pct === null
            ? 'Pergamino seco / cereza trazada'
            : `Pergamino seco / cereza trazada · línea: ${fmtNumber(charts.yield_reference_pct, 1)} % del año anterior`
        }
      >
        <FarmChart
          chart={charts.yield_by_unit}
          format={asPct}
          horizontal
          zoom
          reference={charts.yield_reference_pct === null ? undefined : { value: charts.yield_reference_pct, label: 'Histórico' }}
        />
      </ChartCard>
      <ChartCard title="Producción por variedad" subtitle="Pergamino seco según la variedad de los lotes de origen">
        {charts.by_variety.labels.length ? <DonutChart chart={toRecharts(charts.by_variety)} format={asKg} /> : <NoData />}
      </ChartCard>
      <ChartCard title="Costo de recolección" subtitle="Pesos por kg de cereza pesada, por mes">
        <FarmChart chart={charts.picking_cost} format={asCop} asLine />
      </ChartCard>
      <div className="xl:col-span-2">
        <ChartCard title="Café en proceso" subtitle="Lo que hay ahora en cada etapa (cereza, café lavado y pergamino seco)">
          <FarmChart chart={charts.pipeline} format={asKg} horizontal stacked height={140} />
        </ChartCard>
      </div>
    </div>
  )
}

/** Gráficas de calidad y sanidad (§3.3) */
export function QualitySection({ charts }: { charts: QualityCharts }) {
  const unit = charts.unit
  const [low, high] = charts.humidity_range
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <ChartCard title="Distribución de puntajes" subtitle="Secados evaluados en pergamino, en rangos de 2 puntos">
        <FarmChart chart={charts.score_distribution} format={asCount} />
      </ChartCard>
      <ChartCard title="Puntaje por variedad" subtitle="Promedio ponderado por la cereza de cada variedad">
        <FarmChart chart={charts.score_by_variety} format={asScore} horizontal zoom />
      </ChartCard>
      <ChartCard title={`Puntaje y defectos por ${unitName(unit)}`} subtitle="Puntaje a la izquierda; % de defectos a la derecha">
        <FarmChart chart={charts.score_defects_by_unit} format={asScore} rightAxis={['Defectos (%)']} />
      </ChartCard>
      <ChartCard title="Evolución de la calidad" subtitle="Puntaje promedio por mes">
        <FarmChart chart={charts.score_evolution} format={asScore} asLine />
      </ChartCard>
      <ChartCard title={`Broca por ${unitName(unit)}`} subtitle="Último muestreo de los ciclos activos; la línea es el umbral de alerta">
        <FarmChart chart={charts.broca_by_unit} format={asPct} lines={['Umbral (%)']} />
      </ChartCard>
      <ChartCard title={`Roya por ${unitName(unit)}`} subtitle="Último muestreo de los ciclos activos">
        <FarmChart chart={charts.roya_by_unit} format={asPct} />
      </ChartCard>
      <div className="xl:col-span-2">
        <ChartCard
          title="Humedad final de los secados"
          subtitle={
            low !== null && high !== null
              ? `En verde, dentro del rango de ${fmtNumber(low, 1)} a ${fmtNumber(high, 1)} %; en ámbar, fuera`
              : 'Secados cerrados en el periodo'
          }
        >
          <FarmChart
            chart={charts.humidity_distribution}
            format={asCount}
            highlight={(label) => humidityBinInside(label, charts.humidity_range)}
          />
        </ChartCard>
      </div>
    </div>
  )
}
