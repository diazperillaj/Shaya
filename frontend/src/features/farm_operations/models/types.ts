/**
 * Modelos del módulo de cultivo.
 *
 * Los valores decimales llegan de la API como texto y se convierten a
 * número en los servicios; los campos opcionales vacíos son `null`.
 */

import type { BarChartDataApi } from '../../../components/charts/chartData'

export type PlotStatus = 'active' | 'closed'

export type PlotEventType =
  | 'zoca'
  | 'partial_replant'
  | 'shade_change'
  | 'closure'
  | 'reopening'
  | 'other'

export type SupplyType =
  | 'fertilizer'
  | 'phytosanitary'
  | 'herbicide'
  | 'amendment'
  | 'other'

/* =======================
   FINCAS
======================= */

export interface Farm {
  id: number
  farmer: { id: number; full_name: string }
  name: string
  village: string
  municipality: string
  altitude: number | null
  total_area: number | null
  latitude: number | null
  longitude: number | null
  active: boolean
  observations: string | null
  created_at: string
  active_plots: number
}

export interface FarmPayload {
  /** Solo al crear, y solo lo indica el administrador */
  farmer_id?: number | null
  name: string
  village: string
  municipality: string
  altitude: number | null
  total_area: number | null
  latitude: number | null
  longitude: number | null
  observations: string | null
  /** Solo al editar */
  active?: boolean
}

/* =======================
   LOTES
======================= */

/** Datos del formulario de lote: terreno, siembra y procedencia de la semilla */
export interface PlotFields {
  name: string
  area: number | null
  slope: number | null
  soil_type: string | null
  location: string | null
  variety: string
  planting_date: string | null
  initial_age_years: number | null
  seedling_count: number | null
  row_spacing_m: number | null
  plant_spacing_m: number | null
  shade_type: string | null
  seed_supplier: string | null
  seed_origin_place: string | null
  seed_purchase_date: string | null
  seed_cost: number | null
  observations: string | null
}

export interface Plot extends PlotFields {
  id: number
  farm_id: number
  farm_name: string
  status: PlotStatus
  renewed_from_plot_id: number | null
  renewed_by_plot_id: number | null
  closed_at: string | null
  created_at: string
  /** Años desde la siembra o la última zoca (congelada al cierre) */
  effective_age_years: number
  last_zoca_date: string | null
  active_cycle: ActiveCycleRef | null
}

export interface ActiveCycleRef {
  id: number
  cycle_number: number
  start_date: string
}

export interface PlotCreatePayload extends PlotFields {
  farm_id: number
  renewed_from_plot_id?: number | null
}

/** Terreno de un lote cerrado, para precargar el lote que lo renueva */
export interface RenewalDefaults {
  farm_id: number
  renewed_from_plot_id: number
  name: string
  area: number | null
  slope: number | null
  soil_type: string | null
  location: string | null
}

export interface PlotEvent {
  id: number
  plot_id: number
  event_type: PlotEventType
  other_detail: string | null
  event_date: string
  description: string | null
  created_at: string
}

export interface PlotEventPayload {
  event_type: PlotEventType
  event_date: string
  other_detail: string | null
  description: string | null
}

/* =======================
   ALERTAS
======================= */

export type AlertParameter =
  | 'fertilization_reminder_days'
  | 'irrigation_reminder_days'
  | 'phytosanitary_reminder_days'
  | 'weeding_reminder_days'
  | 'harvest_reminder_days'
  | 'inactivity_alert_days'
  | 'max_drying_days'
  | 'min_final_humidity'
  | 'max_final_humidity'
  | 'min_fermentation_hours'
  | 'max_fermentation_hours'
  | 'broca_alert_pct'

/** Nivel del que sale un valor: el lote, la finca o el valor por defecto */
export type AlertSource = 'plot' | 'farm' | 'default'

export interface ResolvedAlertValue {
  /** Valor efectivo; `null` = recordatorio desactivado */
  value: number | null
  source: AlertSource
  /** Valor que aplicaría sin el valor propio del nivel consultado */
  inherited_value: number | null
  inherited_source: Exclude<AlertSource, 'plot'>
}

export interface ResolvedAlertConfig {
  farm_id: number
  plot_id: number | null
  values: Record<AlertParameter, ResolvedAlertValue>
}

/** Valores propios de un nivel; `null` hereda del nivel superior */
export type AlertConfigPayload = Record<AlertParameter, number | null>

/* =======================
   INSUMOS Y EMPLEADOS
======================= */

export interface Supply {
  id: number
  name: string
  supply_type: SupplyType
  other_detail: string | null
  unit: string
  composition: string | null
  active: boolean
  created_at: string
}

export interface SupplyPayload {
  name: string
  supply_type: SupplyType
  other_detail: string | null
  unit: string
  composition: string | null
}

export interface Employee {
  id: number
  farm_id: number
  full_name: string
  document: string | null
  phone: string | null
  active: boolean
  observations: string | null
  created_at: string
}

export interface EmployeePayload {
  full_name: string
  document: string | null
  phone: string | null
  observations: string | null
}

/* =======================
   CUENTAS DE CAFICULTOR
======================= */

export interface FarmerAccount {
  farmer_id: number
  full_name: string
  document: string | null
  phone: string | null
  farms: number
  user_id: number | null
  username: string | null
  /** `farmer`, o el rol de personal si la persona ya trabaja en Shaya */
  account_role: string | null
}

export interface NewFarmerAccountPayload {
  farm_name: string
  village: string
  municipality: string
  person: {
    full_name: string
    document: string | null
    phone: string
    email: string | null
  }
  username: string
  password: string
}

/* =======================
   CICLOS
======================= */

export type CycleStatus = 'active' | 'closed'

export interface CropCycle {
  id: number
  plot_id: number
  plot_name: string
  farm_id: number
  cycle_number: number
  start_date: string
  end_date: string | null
  status: CycleStatus
  observations: string | null
  created_at: string
}

/** Labores de un tipo dentro del ciclo */
export interface RecordSummary {
  kind: LaborKind
  count: number
  last_date: string | null
  /** Solo en las labores con costo */
  total_cost: number | null
}

export interface CycleDetail extends CropCycle {
  summary: RecordSummary[]
}

export interface CycleUpdatePayload {
  start_date: string
  /** Solo en ciclos cerrados */
  end_date: string | null
  observations: string | null
}

/* =======================
   LABORES
======================= */

/** Tipo de labor, igual al segmento de su ruta en la API */
export type LaborKind =
  | 'fertilizations'
  | 'phytosanitary-apps'
  | 'irrigations'
  | 'pest-monitorings'
  | 'cultural-practices'
  | 'flowering-records'

export type FertilizationMethod = 'soil' | 'foliar'
export type Severity = 'low' | 'medium' | 'high'
export type Intensity = 'low' | 'medium' | 'high'
export type CulturalPracticeType = 'weeding' | 'pruning' | 'shade_regulation' | 'amendment' | 'other'

interface LaborBase {
  id: number
  crop_cycle_id: number
  cycle_number: number
  plot_id: number
  plot_name: string
  observations: string | null
  created_at: string
}

export interface SupplyRef {
  id: number
  name: string
  unit: string
}

export interface Fertilization extends LaborBase {
  supply_id: number
  supply: SupplyRef
  application_date: string
  method: FertilizationMethod
  quantity: number
  dose_per_tree_g: number | null
  cost: number | null
}

export interface PhytosanitaryApp extends LaborBase {
  supply_id: number
  supply: SupplyRef
  application_date: string
  target: string
  quantity: number
  dose_description: string | null
  cost: number | null
}

export interface Irrigation extends LaborBase {
  irrigation_date: string
  method: string | null
  duration_minutes: number | null
  volume_liters: number | null
}

export interface PestMonitoring extends LaborBase {
  monitoring_date: string
  broca_pct: number | null
  roya_pct: number | null
  other_pest: string | null
  other_pest_pct: number | null
  severity: Severity | null
}

export interface CulturalPractice extends LaborBase {
  practice_type: CulturalPracticeType
  other_detail: string | null
  practice_date: string
  cost: number | null
}

export interface FloweringRecord extends LaborBase {
  flowering_date: string
  intensity: Intensity
}

export interface LaborRecords {
  fertilizations: Fertilization
  'phytosanitary-apps': PhytosanitaryApp
  irrigations: Irrigation
  'pest-monitorings': PestMonitoring
  'cultural-practices': CulturalPractice
  'flowering-records': FloweringRecord
}

/** Un registro de cualquier labor, con su tipo */
export type AnyLabor = { [K in LaborKind]: { kind: K; record: LaborRecords[K] } }[LaborKind]

/** Cuerpo de una labor: campos propios sin id ni datos del ciclo */
export type LaborPayload = Record<string, string | number | null>

/* =======================
   CLIMA Y SUELO
======================= */

export interface ClimateRecord {
  id: number
  farm_id: number
  plot_id: number | null
  plot_name: string | null
  record_date: string
  rainfall_mm: number | null
  temp_min_c: number | null
  temp_max_c: number | null
  observations: string | null
  created_at: string
}

export interface ClimatePayload {
  plot_id: number | null
  record_date: string
  rainfall_mm: number | null
  temp_min_c: number | null
  temp_max_c: number | null
  observations: string | null
}

export interface SoilAnalysis {
  id: number
  plot_id: number
  plot_name: string
  analysis_date: string
  ph: number | null
  organic_matter_pct: number | null
  nitrogen: number | null
  phosphorus: number | null
  potassium: number | null
  texture: string | null
  laboratory: string | null
  observations: string | null
  created_at: string
}

export type SoilAnalysisPayload = Omit<SoilAnalysis, 'id' | 'plot_id' | 'plot_name' | 'created_at'>

/* =======================
   COSECHAS, JORNALES Y PAGOS
======================= */

export type HarvestStatus = 'open' | 'closed'
export type HarvestPaymentType = 'per_kg' | 'per_day'
export type LaborActivity =
  | 'weeding'
  | 'pruning'
  | 'fertilization'
  | 'phytosanitary'
  | 'irrigation'
  | 'shade_regulation'
  | 'maintenance'
  | 'other'

export interface HarvestWork {
  id: number
  harvest_id: number
  employee_id: number
  employee_name: string
  work_date: string
  payment_type: HarvestPaymentType
  kg_collected: number | null
  rate_per_kg: number | null
  day_value: number | null
  total_value: number
  paid: boolean
  paid_at: string | null
  created_at: string
}

export interface HarvestWorkPayload {
  employee_id: number
  work_date: string
  payment_type: HarvestPaymentType
  kg_collected: number | null
  /** `null` usa la tarifa de la cosecha */
  rate_per_kg: number | null
  /** `null` usa el jornal de la cosecha */
  day_value: number | null
}

export interface Harvest {
  id: number
  crop_cycle_id: number
  cycle_number: number
  plot_id: number
  plot_name: string
  farm_id: number
  pass_number: number
  start_date: string
  end_date: string | null
  status: HarvestStatus
  rate_per_kg: number | null
  rate_per_day: number | null
  total_cherry_kg: number | null
  observations: string | null
  created_at: string
  works_count: number
  /** Suma de los kg anotados en la recolección */
  kg_registered: number
  value_total: number
  value_pending: number
  /** Café cereza ya repartido en beneficios */
  kg_processed: number
}

export interface HarvestDetail extends Harvest {
  works: HarvestWork[]
}

export interface HarvestPayload {
  start_date: string
  rate_per_kg: number | null
  rate_per_day: number | null
  observations: string | null
}

export interface HarvestUpdatePayload extends HarvestPayload {
  /** Solo en cosechas cerradas */
  end_date: string | null
  total_cherry_kg: number | null
}

export interface DayLabor {
  id: number
  employee_id: number
  employee_name: string
  farm_id: number
  labor_date: string
  activity_type: LaborActivity
  other_detail: string | null
  plot_id: number | null
  plot_name: string | null
  daily_value: number
  paid: boolean
  paid_at: string | null
  observations: string | null
  created_at: string
}

export interface DayLaborPayload {
  employee_id: number
  labor_date: string
  activity_type: LaborActivity
  other_detail: string | null
  plot_id: number | null
  daily_value: number
  observations: string | null
}

/** Un trabajo por pagar o pagado: recolección de un día o un jornal */
export interface PaymentItem {
  kind: 'harvest_work' | 'day_labor'
  id: number
  farm_id: number
  employee_id: number
  employee_name: string
  item_date: string
  amount: number
  paid: boolean
  paid_at: string | null
  plot_name: string | null
  harvest_id: number | null
  pass_number: number | null
  payment_type: HarvestPaymentType | null
  kg_collected: number | null
  activity_type: LaborActivity | null
  other_detail: string | null
}

export interface PaymentSelection {
  harvest_work_ids: number[]
  day_labor_ids: number[]
}

export interface PaymentResult {
  count: number
  total: number
}

/* =======================
   BENEFICIO, SECADO Y CALIDAD
======================= */

export type ProcessStatus = 'in_progress' | 'completed'
export type FermentationMethod = 'tank' | 'dry' | 'water' | 'other'
export type DryingMethod = 'elba' | 'marquesina' | 'patio' | 'mechanical_silo' | 'other'
export type DryingDestination = 'inventory' | 'direct_sale' | 'stored'
export type QualityStage = 'cherry' | 'parchment'

export interface WetInput {
  harvest_id: number
  cherry_kg: number
  plot_id: number
  plot_name: string
  cycle_number: number
  pass_number: number
  harvest_status: HarvestStatus
}

/** Etapas del beneficio; se registran a medida que ocurren */
export interface WetProcessingStages {
  floats_kg: number | null
  floats_method: string | null
  pulped_at: string | null
  fermentation_start: string | null
  fermentation_end: string | null
  fermentation_method: FermentationMethod | null
  fermentation_other_detail: string | null
  fermentation_decided_by: string | null
  fermentation_criteria: string | null
  ambient_temp_c: number | null
  wash_count: number | null
  washed_kg: number | null
  observations: string | null
}

export interface WetProcessing extends WetProcessingStages {
  id: number
  farm_id: number
  farm_name: string
  status: ProcessStatus
  created_at: string
  /** Café cereza que entró (suma de los aportes) */
  cherry_kg: number
  fermentation_hours: number | null
  /** Café lavado ya repartido en secados */
  washed_kg_dried: number
  inputs: WetInput[]
}

export interface DryingInputRow {
  wet_processing_id: number
  wet_kg: number
  pulped_at: string | null
  washed_kg: number | null
}

export interface HumidityCheck {
  id: number
  check_date: string
  humidity_pct: number
}

export interface CompositionHarvest {
  harvest_id: number
  pass_number: number
  crop_cycle_id: number
  cycle_number: number
  cherry_kg: number
}

export interface CompositionPlot {
  plot_id: number
  plot_name: string
  variety: string
  cherry_kg: number
  share_pct: number
  harvests: CompositionHarvest[]
}

export interface Drying {
  id: number
  farm_id: number
  farm_name: string
  status: ProcessStatus
  method: DryingMethod
  other_detail: string | null
  start_date: string
  end_date: string | null
  final_humidity_pct: number | null
  output_kg: number | null
  packaging: string | null
  sack_count: number | null
  packed_at: string | null
  storage_place: string | null
  destination: DryingDestination | null
  observations: string | null
  created_at: string
  /** Café lavado que entró */
  wet_kg: number
  days: number
  /** Café cereza de las cosechas que terminó en este secado */
  cherry_kg_traced: number
  /** Pergamino seco / cereza trazada */
  yield_pct: number | null
  /** Rango esperado de humedad final (configuración de alertas de la finca) */
  humidity_range: [number | null, number | null]
  parchment_id: number | null
  inputs: DryingInputRow[]
  humidity_checks: HumidityCheck[]
  composition: CompositionPlot[]
}

export interface DryingCompletePayload {
  end_date: string
  final_humidity_pct: number
  output_kg: number
  packaging: string | null
  sack_count: number | null
  packed_at: string | null
  storage_place: string | null
  destination: DryingDestination
  inventory_data: { full_price: number; purchase_date: string } | null
}

export interface QualityEval {
  id: number
  stage: QualityStage
  harvest_id: number | null
  drying_id: number | null
  eval_date: string
  ripe_pct: number | null
  green_pct: number | null
  overripe_pct: number | null
  bored_pct: number | null
  humidity_pct: number | null
  defects_pct: number | null
  yield_factor: number | null
  score: number | null
  observations: string | null
  created_at: string
}

export type QualityEvalPayload = Omit<QualityEval, 'id' | 'stage' | 'harvest_id' | 'drying_id' | 'created_at'>

export interface TraceCycle {
  crop_cycle_id: number
  cycle_number: number
  start_date: string
  end_date: string | null
  status: CycleStatus
  cherry_kg: number
  harvests: { harvest_id: number; pass_number: number; cherry_kg: number }[]
  labors: RecordSummary[]
}

export interface DryingTrace {
  drying: Drying
  plots: (Omit<CompositionPlot, 'harvests'> & { cycles: TraceCycle[] })[]
  wet_processings: {
    wet_processing_id: number
    pulped_at: string | null
    cherry_kg: number
    washed_kg: number | null
    wet_kg: number
  }[]
}

// ── Dashboard ─────────────────────────────────────────────────────────────

export type AlertSeverity = 'high' | 'medium' | 'info'

export interface FarmAlert {
  type: string
  severity: AlertSeverity
  farm_id: number
  farm_name: string
  plot_id: number | null
  plot_name: string | null
  /** A qué enlaza: lote y ciclo, cosecha, beneficio, secado o pagos de la finca */
  entity: Partial<Record<'plot_id' | 'crop_cycle_id' | 'harvest_id' | 'wet_processing_id' | 'drying_id' | 'farm_id', number>>
  message: string
  value: number | null
  threshold: number | null
  since: string | null
}

export interface InProcess {
  count: number
  kg: number
  oldest_days: number | null
}

export interface DashboardSummary {
  period: { date_from: string; date_to: string }
  farms_active: number
  plots_active: number
  area_by_variety: { variety: string; area_ha: number }[]
  cycles_active: number
  harvests_open: number
  wet_in_progress: InProcess
  drying_in_progress: InProcess
  stored_parchment_kg: number
  pending_payments: number
  stored_dryings: {
    drying_id: number
    farm_id: number
    farm_name: string
    end_date: string
    output_kg: number
    days: number
  }[]
  cherry_kg: number
  parchment_kg: number
  yield_pct: number | null
  yield_history_pct: number | null
  harvest_cost: number
  score_avg: number | null
  evaluations: number
}

export type ChartUnit = 'farm' | 'plot'

export interface ProductionCharts {
  unit: ChartUnit
  monthly: BarChartDataApi
  by_unit: BarChartDataApi
  yield_by_unit: BarChartDataApi
  yield_reference_pct: number | null
  by_variety: BarChartDataApi
  picking_cost: BarChartDataApi
  pipeline: BarChartDataApi
}

export interface QualityCharts {
  unit: ChartUnit
  score_distribution: BarChartDataApi
  score_by_variety: BarChartDataApi
  score_defects_by_unit: BarChartDataApi
  score_evolution: BarChartDataApi
  broca_by_unit: BarChartDataApi
  roya_by_unit: BarChartDataApi
  humidity_distribution: BarChartDataApi
  humidity_range: [number | null, number | null]
}

export interface Season {
  label: string
  date_from: string
  date_to: string
  harvests: number
  cherry_kg: number
  open: boolean
}

export interface CycleState {
  crop_cycle_id: number
  cycle_number: number
  plot_id: number
  plot_name: string
  farm_id: number
  farm_name: string
  start_date: string
  days: number
  last_labor: { kind: LaborKind; date: string } | null
  harvest_status: 'waiting' | 'open' | 'harvested'
  estimated_harvest: string | null
  alerts: number
}

export interface FarmRanking {
  farm_id: number
  farm_name: string
  plots_active: number
  cherry_kg: number
  parchment_kg: number
  yield_pct: number | null
  score_avg: number | null
  alerts_high: number
  alerts_medium: number
  alerts_info: number
  broca_pct: number | null
  roya_pct: number | null
  broca_threshold: number | null
  stored_kg: number
}
