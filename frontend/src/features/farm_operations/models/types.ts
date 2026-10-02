/**
 * Modelos del módulo de cultivo.
 *
 * Los valores decimales llegan de la API como texto y se convierten a
 * número en los servicios; los campos opcionales vacíos son `null`.
 */

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
