import { FlaskConical } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { FormSection, SelectField, TextField } from '../components/fields'
import { textOrNull, useFormValues } from '../components/useFormValues'
import { SUPPLY_TYPE_LABELS, UNIT_SUGGESTIONS } from '../models/labels'
import type { Supply, SupplyType } from '../models/types'
import { createSupply, updateSupply } from '../services/supplies.api'

interface SupplyFormDialogProps {
  supply?: Supply
  /** Tipo preseleccionado al crear desde un formulario de labor */
  defaultType?: SupplyType
  /** Nombre ya escrito en la búsqueda del formulario de labor */
  initialName?: string
  onClose: () => void
  onSaved: (supply: Supply) => void
}

/**
 * Crear o editar un insumo del catálogo compartido.
 *
 * Se usa desde el catálogo y, en las labores, para crear un insumo al vuelo
 * sin salir del formulario.
 */
export default function SupplyFormDialog({
  supply,
  defaultType = 'fertilizer',
  initialName = '',
  onClose,
  onSaved,
}: SupplyFormDialogProps) {
  const { values, bind, requireFields } = useFormValues({
    name: supply?.name ?? initialName,
    supply_type: supply?.supply_type ?? defaultType,
    other_detail: supply?.other_detail ?? '',
    unit: supply?.unit ?? 'kg',
    composition: supply?.composition ?? '',
  })
  const isOther = values.supply_type === 'other'

  const handleSubmit = async () => {
    if (!requireFields(isOther ? ['name', 'unit', 'other_detail'] : ['name', 'unit'])) return
    const payload = {
      name: values.name.trim(),
      supply_type: values.supply_type as SupplyType,
      other_detail: isOther ? textOrNull(values.other_detail) : null,
      unit: values.unit.trim(),
      composition: textOrNull(values.composition),
    }
    onSaved(supply ? await updateSupply(supply.id, payload) : await createSupply(payload))
  }

  return (
    <FormDialog
      title={supply ? 'Editar insumo' : 'Nuevo insumo'}
      description="El catálogo es compartido: lo usan todas las fincas."
      icon={FlaskConical}
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection>
        <TextField label="Nombre" required wide placeholder="Ej. Urea, DAP, Lorsban" {...bind('name')} />
        <SelectField
          label="Tipo"
          required
          options={Object.entries(SUPPLY_TYPE_LABELS).map(([value, label]) => ({ value, label }))}
          {...bind('supply_type')}
        />
        <TextField label="Unidad" required suggestions={UNIT_SUGGESTIONS} {...bind('unit')} />
        {isOther && <TextField label="¿Qué tipo de insumo?" required wide {...bind('other_detail')} />}
        <TextField
          label="Composición"
          wide
          hint="Ingrediente activo o grado, p. ej. 25-4-24."
          {...bind('composition')}
        />
      </FormSection>
    </FormDialog>
  )
}
