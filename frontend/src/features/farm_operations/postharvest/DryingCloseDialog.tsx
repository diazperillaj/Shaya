import { useState } from 'react'
import { PackageCheck, Warehouse } from 'lucide-react'
import FormDialog from '../components/FormDialog'
import { DateField, FormSection, NumberField, TextField } from '../components/fields'
import { numberOrNull, textOrNull, useFormValues } from '../components/useFormValues'
import WeightField from '../components/WeightField'
import { toKg } from '../components/weight'
import type { WeightUnit } from '../components/weight'
import { fmtMoney, fmtNumber, todayIso } from '../format'
import { DEFAULT_PACKAGING, DRYING_DESTINATION_LABELS, KG_PER_CARGA } from '../models/labels'
import type { Drying, DryingDestination } from '../models/types'
import { completeDrying, sendDryingToInventory } from '../services/postharvest.api'

/** Valor del lote con la regla de 3 del inventario: kg × precio por carga / 125 */
const purchasePrice = (kg: number | null, fullPrice: number | null) =>
  kg !== null && fullPrice !== null ? (kg * fullPrice) / KG_PER_CARGA : null

/**
 * Cerrar el secado: pergamino seco, humedad final, empaque y destino. Con
 * destino inventario se registra el pergamino con el precio por carga que
 * asigna el productor (decisión C1), en la misma operación.
 */
export function DryingCloseDialog({ drying, onClose, onSaved }: { drying: Drying; onClose: () => void; onSaved: () => void }) {
  const { values, bind, requireFields } = useFormValues({
    end_date: todayIso(),
    final_humidity_pct: '',
    output_kg: '',
    packaging: DEFAULT_PACKAGING,
    sack_count: '',
    packed_at: todayIso(),
    storage_place: '',
    destination: 'inventory',
    full_price: '',
    purchase_date: todayIso(),
  })
  const [unit, setUnit] = useState<WeightUnit>('kg')
  const toInventory = values.destination === 'inventory'
  const output = bind('output_kg')
  const humidityField = bind('final_humidity_pct')
  const outputKg = toKg(values.output_kg, unit)
  const humidity = numberOrNull(values.final_humidity_pct)
  const [min, max] = drying.humidity_range
  const outOfRange = humidity !== null && ((min !== null && humidity < min) || (max !== null && humidity > max))
  const yieldPct = outputKg !== null && drying.cherry_kg_traced > 0 ? (outputKg / drying.cherry_kg_traced) * 100 : null

  const handleSubmit = async () => {
    const required = ['end_date', 'final_humidity_pct', 'output_kg'] as const
    if (!requireFields(toInventory ? [...required, 'full_price', 'purchase_date'] : [...required])) return
    await completeDrying(drying.id, {
      end_date: values.end_date,
      final_humidity_pct: humidity ?? 0,
      output_kg: outputKg ?? 0,
      packaging: textOrNull(values.packaging),
      sack_count: numberOrNull(values.sack_count),
      packed_at: values.packed_at || null,
      storage_place: textOrNull(values.storage_place),
      destination: values.destination as DryingDestination,
      inventory_data: toInventory
        ? { full_price: numberOrNull(values.full_price) ?? 0, purchase_date: values.purchase_date }
        : null,
    })
    onSaved()
  }

  return (
    <FormDialog
      wide
      title={`Cerrar el secado ${drying.id}`}
      description={`Entró ${fmtNumber(drying.wet_kg, 1, 'kg')} de café lavado (${fmtNumber(drying.cherry_kg_traced, 1, 'kg')} de cereza).`}
      icon={PackageCheck}
      submitLabel={toInventory ? 'Cerrar y registrar en inventario' : 'Cerrar secado'}
      onClose={onClose}
      onSubmit={handleSubmit}
    >
      <FormSection title="Secado">
        <DateField label="Fecha de fin" required max={todayIso()} {...bind('end_date')} />
        <NumberField
          label="Humedad final"
          required
          unit="%"
          step="0.01"
          min="0"
          hint={`Esperado: ${fmtNumber(min, 1)} a ${fmtNumber(max, 1, '%')}.`}
          {...humidityField}
          error={
            humidityField.error ??
            (outOfRange
              ? `Fuera del rango esperado (${fmtNumber(min, 1)} a ${fmtNumber(max, 1, '%')}): se puede guardar igual.`
              : undefined)
          }
        />
        <WeightField
          label="Pergamino seco"
          required
          hint={yieldPct !== null ? `Rendimiento: ${fmtNumber(yieldPct, 1)} % de la cereza.` : undefined}
          value={output.value}
          error={output.error}
          onChange={output.onChange}
          unit={unit}
          onUnitChange={setUnit}
        />
      </FormSection>

      <FormSection title="Almacenamiento">
        <TextField label="Empaque" wide {...bind('packaging')} />
        <NumberField label="Bultos" min="1" {...bind('sack_count')} />
        <DateField label="Fecha de empaque" max={todayIso()} {...bind('packed_at')} />
        <TextField label="Bodega o lugar" wide {...bind('storage_place')} />
      </FormSection>

      <FormSection title="Destino">
        <div className="grid grid-cols-1 gap-2 sm:col-span-2 sm:grid-cols-3" role="radiogroup">
          {(Object.keys(DRYING_DESTINATION_LABELS) as DryingDestination[]).map((option) => (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={values.destination === option}
              onClick={() => bind('destination').onChange(option)}
              className={`rounded-xl border px-3 py-2.5 text-sm font-medium transition ${
                values.destination === option
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-900'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {DRYING_DESTINATION_LABELS[option]}
            </button>
          ))}
        </div>
        {toInventory && <InventoryFields bind={bind} outputKg={outputKg} fullPrice={numberOrNull(values.full_price)} />}
        {values.destination === 'stored' && (
          <p className="text-xs text-gray-500 sm:col-span-2">Queda en la finca; puedes enviarlo al inventario después.</p>
        )}
      </FormSection>
    </FormDialog>
  )
}

type Bind = (field: 'full_price' | 'purchase_date') => { value: string; error?: string; onChange: (value: string) => void }

function InventoryFields({ bind, outputKg, fullPrice }: { bind: Bind; outputKg: number | null; fullPrice: number | null }) {
  const total = purchasePrice(outputKg, fullPrice)
  return (
    <>
      <NumberField
        label="Precio por carga (125 kg)"
        required
        unit="COP"
        min="0"
        hint="El valor que asignas a tu café: el precio base del mercado o más."
        {...bind('full_price')}
      />
      <DateField label="Fecha de ingreso" required max={todayIso()} {...bind('purchase_date')} />
      {total !== null && (
        <p className="text-sm text-gray-600 sm:col-span-2">
          Valor del lote en inventario: <span className="font-semibold text-gray-900">{fmtMoney(total)}</span>
        </p>
      )}
    </>
  )
}

/** Enviar al inventario el pergamino de un secado guardado en la finca */
export function ToInventoryDialog({ drying, onClose, onSaved }: { drying: Drying; onClose: () => void; onSaved: () => void }) {
  const { values, bind, requireFields } = useFormValues({ full_price: '', purchase_date: todayIso() })

  return (
    <FormDialog
      title="Enviar al inventario"
      description={`${fmtNumber(drying.output_kg, 1, 'kg')} de pergamino seco del secado ${drying.id}.`}
      icon={Warehouse}
      submitLabel="Registrar en inventario"
      onClose={onClose}
      onSubmit={async () => {
        if (!requireFields(['full_price', 'purchase_date'])) return
        await sendDryingToInventory(drying.id, {
          full_price: numberOrNull(values.full_price) ?? 0,
          purchase_date: values.purchase_date,
        })
        onSaved()
      }}
    >
      <FormSection>
        <InventoryFields bind={bind} outputKg={drying.output_kg} fullPrice={numberOrNull(values.full_price)} />
      </FormSection>
    </FormDialog>
  )
}
