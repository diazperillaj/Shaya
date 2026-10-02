import type {
  AlertParameter,
  AlertSource,
  CulturalPracticeType,
  FertilizationMethod,
  Intensity,
  PlotEventType,
  Severity,
  SupplyType,
} from './types'

export const SUPPLY_TYPE_LABELS: Record<SupplyType, string> = {
  fertilizer: 'Fertilizante',
  phytosanitary: 'Fitosanitario',
  herbicide: 'Herbicida',
  amendment: 'Enmienda',
  other: 'Otro',
}

export const PLOT_EVENT_LABELS: Record<PlotEventType, string> = {
  zoca: 'Zoca',
  partial_replant: 'Resiembra parcial',
  shade_change: 'Cambio de sombrío',
  closure: 'Cierre del lote',
  reopening: 'Reapertura',
  other: 'Otro',
}

/** Eventos que se registran a mano (el cierre y la reapertura tienen su acción) */
export const MANUAL_EVENT_TYPES: PlotEventType[] = [
  'zoca',
  'partial_replant',
  'shade_change',
  'other',
]

export const ALERT_SOURCE_LABELS: Record<AlertSource, string> = {
  plot: 'Lote',
  farm: 'Finca',
  default: 'Por defecto',
}

export interface AlertParameterInfo {
  key: AlertParameter
  label: string
  unit: string
  /** Paso del campo numérico: días enteros o porcentajes con decimales */
  step: string
}

/** Parámetros de alertas agrupados como se muestran en la configuración */
export const ALERT_GROUPS: { title: string; parameters: AlertParameterInfo[] }[] = [
  {
    title: 'Recordatorios de labores',
    parameters: [
      { key: 'fertilization_reminder_days', label: 'Fertilización, cada', unit: 'días', step: '1' },
      { key: 'phytosanitary_reminder_days', label: 'Monitoreo de plagas, cada', unit: 'días', step: '1' },
      { key: 'weeding_reminder_days', label: 'Deshierba o plateo, cada', unit: 'días', step: '1' },
      { key: 'irrigation_reminder_days', label: 'Riego, cada', unit: 'días', step: '1' },
      { key: 'harvest_reminder_days', label: 'Próxima pasada de cosecha, a los', unit: 'días', step: '1' },
      { key: 'inactivity_alert_days', label: 'Ciclo sin registros por más de', unit: 'días', step: '1' },
    ],
  },
  {
    title: 'Beneficio y secado',
    parameters: [
      { key: 'min_fermentation_hours', label: 'Fermentación mínima', unit: 'horas', step: '1' },
      { key: 'max_fermentation_hours', label: 'Fermentación máxima', unit: 'horas', step: '1' },
      { key: 'max_drying_days', label: 'Secado de más de', unit: 'días', step: '1' },
      { key: 'min_final_humidity', label: 'Humedad final mínima', unit: '%', step: '0.1' },
      { key: 'max_final_humidity', label: 'Humedad final máxima', unit: '%', step: '0.1' },
    ],
  },
  {
    title: 'Sanidad',
    parameters: [
      { key: 'broca_alert_pct', label: 'Broca igual o mayor a', unit: '%', step: '0.1' },
    ],
  },
]

/** Sugerencias para normalizar los textos libres que alimentan los análisis */
export const VARIETY_SUGGESTIONS = [
  'Castillo', 'Cenicafé 1', 'Colombia', 'Caturra', 'Típica', 'Borbón', 'Tabi', 'Geisha',
]
export const SOIL_SUGGESTIONS = [
  'Franco', 'Franco arcilloso', 'Franco arenoso', 'Arcilloso', 'Arenoso',
]
export const SHADE_SUGGESTIONS = [
  'Libre exposición', 'Guamo', 'Plátano', 'Nogal cafetero', 'Sombrío mixto',
]
export const UNIT_SUGGESTIONS = ['kg', 'g', 'L', 'cc', 'bulto']

export const FERTILIZATION_METHOD_LABELS: Record<FertilizationMethod, string> = {
  soil: 'Edáfica (al suelo)',
  foliar: 'Foliar',
}

export const SEVERITY_LABELS: Record<Severity, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
}

export const INTENSITY_LABELS: Record<Intensity, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
}

export const CULTURAL_PRACTICE_LABELS: Record<CulturalPracticeType, string> = {
  weeding: 'Deshierba o plateo',
  pruning: 'Poda',
  shade_regulation: 'Regulación de sombrío',
  amendment: 'Encalado',
  other: 'Otra',
}

export const TARGET_SUGGESTIONS = [
  'Broca', 'Roya', 'Maleza', 'Cochinilla', 'Minador', 'Gotera', 'Mancha de hierro', 'Llaga macana',
]
export const OTHER_PEST_SUGGESTIONS = ['Cochinilla', 'Minador', 'Mal rosado', 'Gotera', 'Mancha de hierro']
export const IRRIGATION_METHOD_SUGGESTIONS = ['Aspersión', 'Goteo', 'Manguera', 'Microaspersión']
export const TEXTURE_SUGGESTIONS = SOIL_SUGGESTIONS
