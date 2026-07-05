import type { GeneralExpense, GeneralExpenseApi } from '../models/types'

export const mapExpenseFromApi = (e: GeneralExpenseApi): GeneralExpense => ({
  id: e.id,
  expense_date: e.expense_date,
  amount: Number(e.amount),
  category_id: e.category_id,
  category_name: e.category?.name ?? '—',
  payment_method_id: e.payment_method_id ?? undefined,
  payment_method_name: e.payment_method?.name ?? '—',
  description: e.description,
})
