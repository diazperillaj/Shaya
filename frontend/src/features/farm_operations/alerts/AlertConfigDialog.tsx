import { useCallback } from 'react'
import { BellRing } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { FormSection, NumberField } from '../components/fields'
import { Loading } from '../components/ui'
import { useLoader } from '../components/useLoader'
import { numberOrNull, toInput, useFormValues } from '../components/useFormValues'
import { fmtNumber } from '../format'
import { ALERT_GROUPS, ALERT_SOURCE_LABELS } from '../models/labels'
import type {
  AlertConfigPayload,
  AlertParameter,
  ResolvedAlertConfig,
  ResolvedAlertValue,
} from '../models/types'
import {
  deletePlotConfig,
  fetchResolvedConfig,
  saveConfig,
} from '../services/alertConfigs.api'
import type { AlertLevel } from '../services/alertConfigs.api'

interface AlertConfigDialogProps {
  level: AlertLevel
  /** Nombre de la finca o del lote, para el título */
  name: string
  onClose: () => void
}

/**
 * Configurar alertas y recordatorios de una finca o de un lote.
 *
 * Un campo vacío hereda: el lote de la finca, la finca del valor por
 * defecto. Las alertas solo avisan; nunca bloquean una operación.
 */
export default function AlertConfigDialog({ level, name, onClose }: AlertConfigDialogProps) {
  const { kind, id } = level
  const load = useCallback(() => fetchResolvedConfig({ kind, id }), [kind, id])
  const { data: config, error } = useLoader(load)

  return config ? (
    <AlertConfigForm level={level} name={name} config={config} onClose={onClose} />
  ) : (
    <FormDialog title="Alertas" icon={BellRing} onClose={onClose} onSubmit={async () => onClose()} submitLabel="Cerrar">
      {error ? <p className="text-sm text-red-700">{error}</p> : <Loading />}
    </FormDialog>
  )
}

function AlertConfigForm({
  level,
  name,
  config,
  onClose,
}: AlertConfigDialogProps & { config: ResolvedAlertConfig }) {
  const isPlot = level.kind === 'plot'
  const parameters = ALERT_GROUPS.flatMap((group) => group.parameters.map((p) => p.key))
  const hasOwnPlotValues = isPlot && parameters.some((key) => config.values[key].source === 'plot')

  // Solo los valores propios de este nivel van en los campos
  const { values, bind } = useFormValues(
    Object.fromEntries(
      parameters.map((key) => {
        const item = config.values[key]
        return [key, item.source === level.kind ? toInput(item.value) : '']
      }),
    ) as Record<AlertParameter, string>,
  )

  const handleSubmit = async () => {
    const payload = Object.fromEntries(
      parameters.map((key) => [key, numberOrNull(values[key])]),
    ) as AlertConfigPayload
    await saveConfig(level, payload)
    onClose()
  }

  return (
    <FormDialog
      wide
      title={`Alertas ${isPlot ? 'del lote' : 'de la finca'} «${name}»`}
      description={
        isPlot
          ? 'Deja un campo vacío para usar el valor de la finca.'
          : 'Aplica a todos los lotes de la finca. Deja un campo vacío para usar el valor por defecto.'
      }
      icon={BellRing}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        hasOwnPlotValues
          ? {
              label: 'Usar la de la finca',
              confirm: '¿Quitar la configuración propia del lote? Volverá a usar la de la finca.',
              onConfirm: async () => {
                await deletePlotConfig(level.id)
                onClose()
              },
            }
          : undefined
      }
    >
      <p className="text-sm text-gray-500">
        Las alertas solo avisan en el panel; nunca bloquean el registro de labores.
      </p>
      {ALERT_GROUPS.map((group) => (
        <FormSection key={group.title} title={group.title}>
          {group.parameters.map((parameter) => (
            <NumberField
              key={parameter.key}
              label={parameter.label}
              unit={parameter.unit}
              step={parameter.step}
              min="0"
              placeholder={inheritedText(config.values[parameter.key], parameter.unit, false)}
              hint={inheritedText(config.values[parameter.key], parameter.unit, true)}
              {...bind(parameter.key)}
            />
          ))}
        </FormSection>
      ))}
    </FormDialog>
  )
}

/** Valor que aplica si el campo queda vacío, p. ej. «Finca: 90 días» */
function inheritedText(item: ResolvedAlertValue, unit: string, withSource: boolean): string {
  const value =
    item.inherited_value === null
      ? 'desactivado'
      : fmtNumber(item.inherited_value, 2, unit)
  return withSource ? `Si queda vacío: ${value} (${ALERT_SOURCE_LABELS[item.inherited_source].toLowerCase()})` : value
}
