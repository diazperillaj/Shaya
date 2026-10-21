// features/processes/services/processExpenses.api.ts

import type { CreateExpensePayload, GeneralExpense } from '../../expenses/models/types'
import { mapExpenseFromApi } from '../../expenses/mapper/expense.mapper'
import { apiErrorMessage } from '../../../utils/apiError'

/**
 * Crea un gasto general asociado al proceso. Es la única forma de asociar
 * un gasto a un proceso: editarlo o eliminarlo se hace con la API de Gastos.
 */
export const createProcessExpense = async (
  processId: number,
  payload: CreateExpensePayload,
): Promise<GeneralExpense> => {
  const res = await fetch(`/api/v1/process/${processId}/expenses/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const data = await res.json()
  if (!res.ok) throw new Error(apiErrorMessage(data, 'Error creando el gasto'))

  return mapExpenseFromApi(data)
}
