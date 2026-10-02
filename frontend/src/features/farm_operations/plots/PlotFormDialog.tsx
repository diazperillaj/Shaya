import { useState } from 'react'
import { LandPlot } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import {
  DateField,
  FormSection,
  NumberField,
  TextAreaField,
  TextField,
} from '../components/fields'
import { numberOrNull, textOrNull, toInput, useFormValues } from '../components/useFormValues'
import { fmtNumber, todayIso, treesPerHectare } from '../format'
import { SHADE_SUGGESTIONS, SOIL_SUGGESTIONS, VARIETY_SUGGESTIONS } from '../models/labels'
import type { Plot, PlotFields, RenewalDefaults } from '../models/types'
import { createPlot, deletePlot, updatePlot } from '../services/plots.api'

interface PlotFormDialogProps {
  farmId: number
  /** Lote a editar */
  plot?: Plot
  /** Terreno de un lote cerrado que se vuelve a sembrar */
  renewal?: RenewalDefaults
  onClose: () => void
  onSaved: (plot: Plot) => void
  onDeleted?: () => void
}

/** Cómo se registra la siembra: con su fecha, o con la edad de un cultivo ya establecido */
type PlantingMode = 'date' | 'age'

/**
 * Crear, editar o renovar un lote: terreno, siembra y procedencia de la semilla.
 */
export default function PlotFormDialog({
  farmId,
  plot,
  renewal,
  onClose,
  onSaved,
  onDeleted,
}: PlotFormDialogProps) {
  const source = plot ?? renewal
  const [mode, setMode] = useState<PlantingMode>(
    plot && plot.planting_date === null ? 'age' : 'date',
  )

  const { values, bind, requireFields } = useFormValues({
    name: source?.name ?? '',
    location: source?.location ?? '',
    area: toInput(source?.area),
    slope: toInput(source?.slope),
    soil_type: source?.soil_type ?? '',
    variety: plot?.variety ?? '',
    planting_date: plot?.planting_date ?? '',
    initial_age_years: toInput(plot?.initial_age_years),
    seedling_count: toInput(plot?.seedling_count),
    row_spacing_m: toInput(plot?.row_spacing_m),
    plant_spacing_m: toInput(plot?.plant_spacing_m),
    shade_type: plot?.shade_type ?? '',
    seed_supplier: plot?.seed_supplier ?? '',
    seed_origin_place: plot?.seed_origin_place ?? '',
    seed_purchase_date: plot?.seed_purchase_date ?? '',
    seed_cost: toInput(plot?.seed_cost),
    observations: plot?.observations ?? '',
  })

  const density = treesPerHectare(numberOrNull(values.row_spacing_m), numberOrNull(values.plant_spacing_m))

  const handleSubmit = async () => {
    const plantingField = mode === 'date' ? 'planting_date' : 'initial_age_years'
    if (!requireFields(['name', 'variety', plantingField])) return

    const fields: PlotFields = {
      name: values.name.trim(),
      location: textOrNull(values.location),
      area: numberOrNull(values.area),
      slope: numberOrNull(values.slope),
      soil_type: textOrNull(values.soil_type),
      variety: values.variety.trim(),
      planting_date: mode === 'date' ? values.planting_date : null,
      initial_age_years: mode === 'age' ? numberOrNull(values.initial_age_years) : null,
      seedling_count: numberOrNull(values.seedling_count),
      row_spacing_m: numberOrNull(values.row_spacing_m),
      plant_spacing_m: numberOrNull(values.plant_spacing_m),
      shade_type: textOrNull(values.shade_type),
      seed_supplier: textOrNull(values.seed_supplier),
      seed_origin_place: textOrNull(values.seed_origin_place),
      seed_purchase_date: textOrNull(values.seed_purchase_date),
      seed_cost: numberOrNull(values.seed_cost),
      observations: textOrNull(values.observations),
    }
    const saved = plot
      ? await updatePlot(plot.id, fields)
      : await createPlot({ ...fields, farm_id: farmId, renewed_from_plot_id: renewal?.renewed_from_plot_id ?? null })
    onSaved(saved)
  }

  return (
    <FormDialog
      wide
      title={plot ? 'Editar lote' : renewal ? 'Renovar terreno' : 'Nuevo lote'}
      description={
        renewal
          ? `Nueva siembra sobre el terreno del lote «${renewal.name}». Los datos del terreno vienen precargados.`
          : undefined
      }
      icon={LandPlot}
      onClose={onClose}
      onSubmit={handleSubmit}
      destructive={
        plot && onDeleted
          ? {
              label: 'Eliminar lote',
              confirm: `¿Eliminar el lote «${plot.name}»? Solo es posible si no tiene historial.`,
              onConfirm: async () => {
                await deletePlot(plot.id)
                onDeleted()
              },
            }
          : undefined
      }
    >
      <FormSection title="Lote">
        <TextField label="Nombre" required {...bind('name')} />
        <TextField label="Ubicación en la finca" placeholder="Ej. ladera norte" {...bind('location')} />
      </FormSection>

      <FormSection title="Siembra">
        <TextField label="Variedad" required suggestions={VARIETY_SUGGESTIONS} {...bind('variety')} />
        <TextField label="Tipo de sombrío" suggestions={SHADE_SUGGESTIONS} {...bind('shade_type')} />

        <div className="flex flex-col gap-2 sm:col-span-2">
          <span className="text-sm font-medium text-gray-700">¿Cómo registras la siembra?</span>
          <div className="grid grid-cols-2 gap-2">
            {(
              [
                ['date', 'Sé la fecha de siembra'],
                ['age', 'Ya estaba sembrado'],
              ] as [PlantingMode, string][]
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setMode(value)}
                className={`rounded-xl border px-3 py-2 text-sm transition ${
                  mode === value
                    ? 'border-emerald-700 bg-emerald-50 font-medium text-emerald-900'
                    : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        {mode === 'date' ? (
          <DateField label="Fecha de siembra" required max={todayIso()} {...bind('planting_date')} />
        ) : (
          <NumberField
            label="Edad actual del cultivo"
            required
            unit="años"
            step="0.1"
            min="0"
            hint="La edad se seguirá contando desde hoy."
            {...bind('initial_age_years')}
          />
        )}
        <NumberField label="Plántulas" unit="plantas" min="1" {...bind('seedling_count')} />
        <NumberField label="Distancia entre surcos" unit="m" step="0.01" min="0" {...bind('row_spacing_m')} />
        <NumberField
          label="Distancia entre plantas"
          unit="m"
          step="0.01"
          min="0"
          hint={density ? `Densidad: ${fmtNumber(density, 0)} árboles/ha` : undefined}
          {...bind('plant_spacing_m')}
        />
      </FormSection>

      <FormSection title="Terreno">
        <NumberField label="Área" unit="ha" step="0.01" min="0" {...bind('area')} />
        <NumberField label="Pendiente" unit="%" step="0.1" min="0" {...bind('slope')} />
        <TextField label="Tipo de suelo" suggestions={SOIL_SUGGESTIONS} {...bind('soil_type')} />
      </FormSection>

      <FormSection title="Procedencia de la semilla">
        <TextField label="Proveedor o almacén" placeholder="O germinador propio" {...bind('seed_supplier')} />
        <TextField label="Lugar de compra" {...bind('seed_origin_place')} />
        <DateField label="Fecha de compra" max={todayIso()} {...bind('seed_purchase_date')} />
        <NumberField label="Costo" unit="COP" min="0" {...bind('seed_cost')} />
      </FormSection>

      <FormSection>
        <TextAreaField label="Observaciones" {...bind('observations')} />
      </FormSection>
    </FormDialog>
  )
}
