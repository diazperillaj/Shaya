import { useCallback, useState } from 'react'
import { MapPinned } from 'lucide-react'
import { useAuth } from '../../auth/AuthContext'
import type { Farmer } from '../../farmers/models/types'
import { fetchFarmers } from '../../farmers/services/farmer.api'
import FormDialog from '../components/FormDialog'
import {
  CheckboxField,
  FormSection,
  NumberField,
  SelectField,
  TextAreaField,
  TextField,
} from '../components/fields'
import { useLoader } from '../components/useLoader'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import type { Farm, FarmPayload } from '../models/types'
import { createFarm, deleteFarm, updateFarm } from '../services/farms.api'

interface FarmFormDialogProps {
  /** Finca a editar; sin ella, se crea una nueva */
  farm?: Farm
  onClose: () => void
  onSaved: (farm: Farm) => void
  onDeleted?: () => void
}

/**
 * Crear o editar una finca.
 *
 * Al crear, el administrador elige el caficultor dueño; un caficultor
 * registra siempre a su propio nombre.
 */
export default function FarmFormDialog({ farm, onClose, onSaved, onDeleted }: FarmFormDialogProps) {
  const { user } = useAuth()
  const choosesFarmer = !farm && user?.role === 'admin'

  const loadFarmers = useCallback(
    (): Promise<Farmer[]> => (choosesFarmer ? fetchFarmers() : Promise.resolve([])),
    [choosesFarmer],
  )
  const { data: farmers } = useLoader(loadFarmers)

  const [active, setActive] = useState(farm?.active ?? true)
  const { values, bind, requireFields } = useFormValues({
    farmer_id: '',
    name: farm?.name ?? '',
    village: farm?.village ?? '',
    municipality: farm?.municipality ?? '',
    altitude: toInput(farm?.altitude),
    total_area: toInput(farm?.total_area),
    latitude: toInput(farm?.latitude),
    longitude: toInput(farm?.longitude),
    observations: farm?.observations ?? '',
  })

  const handleSubmit = async () => {
    const required = ['name', 'village', 'municipality'] as const
    if (!requireFields(choosesFarmer ? [...required, 'farmer_id'] : [...required])) return

    const payload: FarmPayload = {
      name: values.name.trim(),
      village: values.village.trim(),
      municipality: values.municipality.trim(),
      altitude: numberOrNull(values.altitude),
      total_area: numberOrNull(values.total_area),
      latitude: numberOrNull(values.latitude),
      longitude: numberOrNull(values.longitude),
      observations: textOrNull(values.observations),
    }
    const saved = farm
      ? await updateFarm(farm.id, { ...payload, active })
      : await createFarm({ ...payload, farmer_id: choosesFarmer ? Number(values.farmer_id) : null })
    onSaved(saved)
  }

  return (
    <FormDialog
      title={farm ? 'Editar finca' : 'Nueva finca'}
      icon={MapPinned}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        farm && onDeleted
          ? {
              label: 'Eliminar finca',
              confirm: `¿Eliminar la finca «${farm.name}»? Solo es posible si no tiene lotes ni empleados.`,
              onConfirm: async () => {
                await deleteFarm(farm.id)
                onDeleted()
              },
            }
          : undefined
      }
    >
      <FormSection>
        {choosesFarmer && (
          <SelectField
            label="Caficultor"
            required
            wide
            placeholder={farmers ? 'Elige el caficultor dueño' : 'Cargando caficultores…'}
            options={(farmers ?? []).map((farmer) => ({ value: String(farmer.id), label: farmer.name }))}
            hint="La producción propia se registra a nombre del caficultor que representa a Shaya."
            {...bind('farmer_id')}
          />
        )}
        <TextField label="Nombre" required wide {...bind('name')} />
        <TextField label="Vereda" required {...bind('village')} />
        <TextField label="Municipio" required {...bind('municipality')} />
        <NumberField label="Altitud" unit="m s.n.m." min="0" {...bind('altitude')} />
        <NumberField label="Área total" unit="ha" step="0.01" min="0" {...bind('total_area')} />
        <NumberField label="Latitud" step="0.000001" hint="Opcional, para mapas" {...bind('latitude')} />
        <NumberField label="Longitud" step="0.000001" {...bind('longitude')} />
        <TextAreaField label="Observaciones" {...bind('observations')} />
        {farm && (
          <CheckboxField
            label="Finca activa"
            hint="Una finca inactiva se conserva con su historial, pero deja de aparecer como en operación."
            checked={active}
            onChange={setActive}
          />
        )}
      </FormSection>
    </FormDialog>
  )
}
