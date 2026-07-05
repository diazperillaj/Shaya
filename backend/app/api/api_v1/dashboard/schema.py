from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


# ─── Coffee price ─────────────────────────────────────────────────────────────

class CoffeePriceResponse(BaseModel):
    price_raw: str           # e.g. "$ 2.320.000,00"
    price_value: Optional[float]  # numeric value for display
    source: str
    error: Optional[str] = None


# ─── KPIs ─────────────────────────────────────────────────────────────────────

class DashboardKPIs(BaseModel):
    # Sales
    sales_total_month: float         # total revenue this month
    sales_count_month: int           # number of sales this month
    sales_total_all_time: float      # all-time revenue
    sales_count_all_time: int        # all-time sale count
    # General expenses
    expenses_total_month: float      # total expenses this month
    expenses_count_month: int        # number of expenses this month
    expenses_total_prev_month: float # previous month (for % variation)
    expenses_total_all_time: float   # all-time expenses
    # Net (después de gastos)
    net_month: float                 # sales - expenses this month
    net_all_time: float              # sales - expenses all time
    # Inventory
    parchment_available_kg: float    # total remaining parchment (kg)
    roasted_bags_available: int      # total remaining roasted bags
    roasted_bags_total: int          # total produced roasted bags
    # Coffee price (scraped)
    coffee_price_raw: str
    coffee_price_value: Optional[float]


# ─── Charts ───────────────────────────────────────────────────────────────────

class ChartPoint(BaseModel):
    label: str
    value: float


class ChartSeries(BaseModel):
    name: str
    data: List[float]


class BarChartData(BaseModel):
    labels: List[str]
    series: List[ChartSeries]


class DashboardCharts(BaseModel):
    # Chart 1: Monthly sales revenue (last 6 months)
    sales_by_month: BarChartData
    # Chart 2: Top 5 best-selling products by units sold
    top_products: BarChartData
    # Chart 3: Roasted inventory – available vs sold per product
    inventory_status: BarChartData
    # Chart 4: Ingresos vs Gastos vs Utilidad (last 6 months)
    income_vs_expenses: BarChartData
    # Chart 5: General expenses grouped by category (donut in the front)
    expenses_by_category: BarChartData
    # Chart 6: Completed sales grouped by payment method (donut in the front)
    sales_by_payment_method: BarChartData
