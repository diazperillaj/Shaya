import type {
  AlertConfigPayload,
  ResolvedAlertConfig,
  ResolvedAlertValue,
} from '../models/types'
import { request, toNumber } from './http'

/** Nivel de configuración: una finca o un lote */
export type AlertLevel = { kind: 'farm' | 'plot'; id: number }

type ResolvedValueApi = Omit<ResolvedAlertValue, 'value' | 'inherited_value'> & {
  value: string | null
  inherited_value: string | null
}

type ResolvedApi = Omit<ResolvedAlertConfig, 'values'> & {
  values: Record<string, ResolvedValueApi>
}

const mapResolved = (config: ResolvedApi): ResolvedAlertConfig => ({
  ...config,
  values: Object.fromEntries(
    Object.entries(config.values).map(([key, item]) => [
      key,
      { ...item, value: toNumber(item.value), inherited_value: toNumber(item.inherited_value) },
    ]),
  ) as ResolvedAlertConfig['values'],
})

export const fetchResolvedConfig = async ({ kind, id }: AlertLevel): Promise<ResolvedAlertConfig> =>
  mapResolved(await request<ResolvedApi>(
    `/alert-configs/resolved/${kind}/${id}`,
    'Error obteniendo la configuración de alertas',
  ))

export const saveConfig = async (
  { kind, id }: AlertLevel,
  payload: AlertConfigPayload,
): Promise<ResolvedAlertConfig> =>
  mapResolved(await request<ResolvedApi>(
    `/alert-configs/${kind}/${id}`,
    'Error guardando la configuración de alertas',
    { method: 'PUT', body: payload },
  ))

/** Quita la configuración propia del lote: vuelve a heredar de la finca */
export const deletePlotConfig = async (plotId: number): Promise<void> => {
  await request(`/alert-configs/plot/${plotId}`, 'Error quitando la configuración del lote', {
    method: 'DELETE',
  })
}
