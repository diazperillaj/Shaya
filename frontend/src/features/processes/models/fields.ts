import type { TableField } from '../../../models/common'
import type { ProcessExpense } from './types'

/**
 * Etiquetas en español para las categorías de gastos de proceso.
 * Los valores coinciden con el enum del backend (ProcessExpenseCategoryEnum).
 */
export const PROCESS_EXPENSE_CATEGORY_LABELS: Record<string, string> = {
  transport: 'Transporte',
  labor: 'Mano de obra',
  supplies: 'Insumos',
  other: 'Otro',
}

/**
 * Campos del formulario de gastos de proceso.
 * Consumidos por el Modal genérico.
 */
export const ProcessExpenseFields: TableField<ProcessExpense>[] = [
  {
    accessor: 'category',
    header: 'Categoría',
    type: 'select',
    options: Object.entries(PROCESS_EXPENSE_CATEGORY_LABELS).map(
      ([value, label]) => ({ label, value }),
    ),
  },
  { accessor: 'amount', header: 'Valor total del gasto', type: 'number' },
  { accessor: 'expense_date', header: 'Fecha', type: 'date' },
  { accessor: 'observations', header: 'Observaciones', type: 'textarea' },
]
