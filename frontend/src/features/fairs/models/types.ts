// ─── Enums ────────────────────────────────────────────────────────────────────

export type FairStatus = 'open' | 'closed'
export type ExpenseCategory = 'food' | 'supplies' | 'transport' | 'other'

// ─── API shapes (raw from backend) ───────────────────────────────────────────

export interface FairInventoryApi {
  id: number
  fair_id: number
  detail_roasted_coffee_id: number
  detail_roasted_coffee?: {
    id: number
    roasted_coffee_id: number
    product_id: number
    product?: { id: number; name: string; quantity: number }
    quantity: number
    remaining_quantity: number
  }
  initial_quantity: number
  remaining_quantity: number
  unit_value: string
}

export interface FairSaleApi {
  id: number
  fair_id: number
  fair_inventory_id: number
  fair_inventory?: FairInventoryApi
  payment_method_id: number
  payment_method?: { id: number; name: string } | null
  sale_datetime: string
  quantity: number
  unit_value: string
  total: string
  observations?: string
}

export interface FairExpenseApi {
  id: number
  fair_id: number
  user_id: number
  user?: { id: number; username: string; role: string; person: { id: number; full_name: string } }
  category: string
  description: string
  amount: string
  expense_datetime: string
}

export interface FairApi {
  id: number
  name: string
  location?: string
  start_datetime: string
  end_datetime?: string
  status: string
  user_id: number
  user?: { id: number; username: string; role: string; person: { id: number; full_name: string } }
  sale_id?: number
  observations?: string
  inventory: FairInventoryApi[]
  fair_sales: FairSaleApi[]
  expenses: FairExpenseApi[]
}

// ─── Mapped types ─────────────────────────────────────────────────────────────

export interface FairInventory {
  id: number
  fairId: number
  detailRoastedCoffeeId: number
  productName: string
  initialQuantity: number
  remainingQuantity: number
  soldQuantity: number
  unitValue: number
}

export interface FairSale {
  id: number
  fairId: number
  fairInventoryId: number
  productName: string
  paymentMethodId: number
  paymentMethodName: string
  saleDatetime: string
  quantity: number
  unitValue: number
  total: number
  observations?: string
}

export interface FairExpense {
  id: number
  fairId: number
  userId: number
  userName: string
  category: ExpenseCategory
  categoryLabel: string
  description: string
  amount: number
  expenseDatetime: string
}

export interface Fair {
  id: number
  name: string
  location?: string
  startDatetime: string
  endDatetime?: string
  status: FairStatus
  userId: number
  userName: string
  saleId?: number
  observations?: string
  inventory: FairInventory[]
  fairSales: FairSale[]
  expenses: FairExpense[]
  // computed
  totalSales: number
  totalExpenses: number
  netProfit: number
}

// ─── Report ───────────────────────────────────────────────────────────────────

export interface FairKPIs {
  total_sales: string
  total_transactions: number
  avg_sale_value: string
  total_expenses: string
  net_profit: string
  margin_percentage: string
  total_bags_assigned: number
  total_bags_sold: number
  total_bags_remaining: number
  inventory_utilization_percentage: string
  duration_hours?: number
}

export interface ChartSeriesApi { name: string; data: number[] }
export interface BarChartDataApi { labels: string[]; series: ChartSeriesApi[] }
export interface PieChartDataApi { labels: string[]; data: number[] }

export interface FairInventoryStatusItem {
  product_name: string
  detail_roasted_coffee_id: number
  initial_quantity: number
  sold_quantity: number
  remaining_quantity: number
  utilization_percentage: string
  revenue: string
}

export interface FairReportApi {
  fair: FairApi
  kpis: FairKPIs
  sales_by_product: BarChartDataApi
  sales_timeline: BarChartDataApi
  expenses_by_category: PieChartDataApi
  inventory_status: FairInventoryStatusItem[]
}

// Recharts format
export interface RechartsPoint { name: string; [key: string]: number | string }

export interface FairReport {
  fair: Fair
  kpis: FairKPIs
  salesByProduct: { data: RechartsPoint[]; keys: string[] }
  salesTimeline: { data: RechartsPoint[]; keys: string[] }
  expensesByCategory: { labels: string[]; data: number[] }
  inventoryStatus: FairInventoryStatusItem[]
}

// ─── Payloads ─────────────────────────────────────────────────────────────────

export interface CreateFairPayload {
  name: string
  location?: string
  start_datetime: string
  observations?: string
}

export interface CreateFairInventoryPayload {
  detail_roasted_coffee_id: number
  initial_quantity: number
  unit_value: number
}

export interface UpdateFairInventoryPayload {
  initial_quantity: number
  unit_value: number
}

export interface CreateFairSalePayload {
  fair_inventory_id: number
  payment_method_id: number
  quantity: number
  unit_value: number
  observations?: string
}

export interface CreateFairExpensePayload {
  category: string
  description: string
  amount: number
}
