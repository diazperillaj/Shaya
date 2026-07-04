import type {
  Fair,
  FairApi,
  FairExpense,
  FairExpenseApi,
  FairInventory,
  FairInventoryApi,
  FairReport,
  FairReportApi,
  FairSale,
  FairSaleApi,
  RechartsPoint,
  BarChartDataApi,
} from '../models/types'

const CATEGORY_LABELS: Record<string, string> = {
  food: 'Alimentación',
  supplies: 'Insumos',
  transport: 'Transporte',
  other: 'Otros',
}

export function mapFairInventoryFromApi(inv: FairInventoryApi): FairInventory {
  return {
    id: inv.id,
    fairId: inv.fair_id,
    detailRoastedCoffeeId: inv.detail_roasted_coffee_id,
    productName: inv.detail_roasted_coffee?.product?.name ?? `Lote #${inv.detail_roasted_coffee_id}`,
    initialQuantity: inv.initial_quantity,
    remainingQuantity: inv.remaining_quantity,
    soldQuantity: inv.initial_quantity - inv.remaining_quantity,
    unitValue: parseFloat(inv.unit_value),
  }
}

export function mapFairSaleFromApi(sale: FairSaleApi): FairSale {
  const productName =
    sale.fair_inventory?.detail_roasted_coffee?.product?.name ??
    `Inv #${sale.fair_inventory_id}`
  return {
    id: sale.id,
    fairId: sale.fair_id,
    fairInventoryId: sale.fair_inventory_id,
    productName,
    saleDatetime: sale.sale_datetime,
    quantity: sale.quantity,
    unitValue: parseFloat(sale.unit_value),
    total: parseFloat(sale.total),
    observations: sale.observations,
  }
}

export function mapFairExpenseFromApi(exp: FairExpenseApi): FairExpense {
  return {
    id: exp.id,
    fairId: exp.fair_id,
    userId: exp.user_id,
    userName: exp.user?.person?.full_name ?? exp.user?.username ?? `#${exp.user_id}`,
    category: exp.category as any,
    categoryLabel: CATEGORY_LABELS[exp.category] ?? exp.category,
    description: exp.description,
    amount: parseFloat(exp.amount),
    expenseDatetime: exp.expense_datetime,
  }
}

export function mapFairFromApi(fair: FairApi): Fair {
  const inventory = fair.inventory.map(mapFairInventoryFromApi)
  const fairSales = fair.fair_sales.map(mapFairSaleFromApi)
  const expenses = fair.expenses.map(mapFairExpenseFromApi)

  const totalSales = fairSales.reduce((sum, s) => sum + s.total, 0)
  const totalExpenses = expenses.reduce((sum, e) => sum + e.amount, 0)

  return {
    id: fair.id,
    name: fair.name,
    location: fair.location,
    startDatetime: fair.start_datetime,
    endDatetime: fair.end_datetime,
    status: fair.status as any,
    userId: fair.user_id,
    userName: fair.user?.person?.full_name ?? fair.user?.username ?? `#${fair.user_id}`,
    saleId: fair.sale_id,
    observations: fair.observations,
    inventory,
    fairSales,
    expenses,
    totalSales,
    totalExpenses,
    netProfit: totalSales - totalExpenses,
  }
}

function toRecharts(chart: BarChartDataApi): { data: RechartsPoint[]; keys: string[] } {
  const data: RechartsPoint[] = chart.labels.map((label, i) => {
    const point: RechartsPoint = { name: label }
    for (const series of chart.series) {
      point[series.name] = series.data[i] ?? 0
    }
    return point
  })
  return { data, keys: chart.series.map((s) => s.name) }
}

export function mapFairReportFromApi(report: FairReportApi): FairReport {
  return {
    fair: mapFairFromApi(report.fair),
    kpis: report.kpis,
    salesByProduct: toRecharts(report.sales_by_product),
    salesTimeline: toRecharts(report.sales_timeline),
    expensesByCategory: { labels: report.expenses_by_category.labels, data: report.expenses_by_category.data },
    inventoryStatus: report.inventory_status,
  }
}
