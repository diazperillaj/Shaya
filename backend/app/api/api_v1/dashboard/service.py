import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import httpx
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.api.api_v1.dashboard.schema import (
    BarChartData,
    ChartSeries,
    CoffeePriceResponse,
    DashboardCharts,
    DashboardKPIs,
)
from app.models.detail_roasted_coffe import DetailRoastedCoffee
from app.models.detail_sale import DetailSale
from app.models.parchment import Parchment
from app.models.product import Product
from app.models.sale import Sale, SaleStatusEnum

COFFEE_PRICE_URL = "https://www.larepublica.co/indicadores-economicos/commodities/cafe"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    # ─── Coffee price ─────────────────────────────────────────────────────────

    def get_coffee_price(self) -> CoffeePriceResponse:
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                response = client.get(COFFEE_PRICE_URL, headers=HEADERS)
                response.raise_for_status()
                html = response.text

            # Multiple <span class="price"> exist; the COP one starts with "$ " (not "US$")
            all_matches = re.findall(
                r'<span[^>]*class=["\']price["\'][^>]*>\s*(.*?)\s*</span>',
                html,
                re.IGNORECASE,
            )
            # Pick the first price that is in COP: starts with "$ " but not "US$"
            raw = next(
                (m.strip() for m in all_matches if m.strip().startswith("$") and not m.strip().startswith("US$")),
                None,
            )
            if not raw:
                return CoffeePriceResponse(
                    price_raw="No disponible",
                    price_value=None,
                    source=COFFEE_PRICE_URL,
                    error="Precio COP no encontrado en la página",
                )
            numeric_value = self._parse_colombian_price(raw)

            return CoffeePriceResponse(
                price_raw=raw,
                price_value=numeric_value,
                source=COFFEE_PRICE_URL,
            )

        except httpx.TimeoutException:
            return CoffeePriceResponse(
                price_raw="No disponible",
                price_value=None,
                source=COFFEE_PRICE_URL,
                error="Timeout al consultar el precio",
            )
        except Exception as exc:
            return CoffeePriceResponse(
                price_raw="No disponible",
                price_value=None,
                source=COFFEE_PRICE_URL,
                error=str(exc),
            )

    # ─── KPIs ─────────────────────────────────────────────────────────────────

    def get_kpis(self) -> DashboardKPIs:
        now = date.today()

        # ── Sales this month (solo completadas: dinero que ya entro) ─────────
        month_sales = (
            self.db.query(func.sum(Sale.total), func.count(Sale.id))
            .filter(
                Sale.status == SaleStatusEnum.completed,
                extract("year", Sale.sale_date) == now.year,
                extract("month", Sale.sale_date) == now.month,
            )
            .one()
        )
        sales_total_month = float(month_sales[0] or 0)
        sales_count_month = month_sales[1] or 0

        # ── All-time sales (solo completadas) ─────────────────────────────────
        all_sales = (
            self.db.query(func.sum(Sale.total), func.count(Sale.id))
            .filter(Sale.status == SaleStatusEnum.completed)
            .one()
        )
        sales_total_all_time = float(all_sales[0] or 0)
        sales_count_all_time = all_sales[1] or 0

        # ── Parchment inventory ───────────────────────────────────────────────
        parchment_available = (
            self.db.query(func.sum(Parchment.remaining_quantity)).scalar() or 0
        )

        # ── Roasted coffee inventory ──────────────────────────────────────────
        roasted = (
            self.db.query(
                func.sum(DetailRoastedCoffee.quantity),
                func.sum(DetailRoastedCoffee.remaining_quantity),
            ).one()
        )
        roasted_bags_total = int(roasted[0] or 0)
        roasted_bags_available = int(roasted[1] or 0)

        # ── Coffee price ──────────────────────────────────────────────────────
        price_data = self.get_coffee_price()

        return DashboardKPIs(
            sales_total_month=sales_total_month,
            sales_count_month=sales_count_month,
            sales_total_all_time=sales_total_all_time,
            sales_count_all_time=sales_count_all_time,
            parchment_available_kg=float(parchment_available),
            roasted_bags_available=roasted_bags_available,
            roasted_bags_total=roasted_bags_total,
            coffee_price_raw=price_data.price_raw,
            coffee_price_value=price_data.price_value,
        )

    # ─── Charts ───────────────────────────────────────────────────────────────

    def get_charts(self) -> DashboardCharts:
        return DashboardCharts(
            sales_by_month=self._sales_by_month(),
            top_products=self._top_products(),
            inventory_status=self._inventory_status(),
        )

    def _sales_by_month(self) -> BarChartData:
        """Total revenue per month for the last 6 months."""
        now = date.today()
        # Build last 6 months in order
        months = []
        for i in range(5, -1, -1):
            month = now.month - i
            year = now.year
            while month <= 0:
                month += 12
                year -= 1
            months.append((year, month))

        MONTH_NAMES = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
        }

        rows = (
            self.db.query(
                extract("year", Sale.sale_date).label("yr"),
                extract("month", Sale.sale_date).label("mo"),
                func.sum(Sale.total).label("total"),
                func.count(Sale.id).label("count"),
            )
            .filter(
                Sale.status == SaleStatusEnum.completed,
                Sale.sale_date >= date(months[0][0], months[0][1], 1),
            )
            .group_by("yr", "mo")
            .all()
        )

        row_map = {(int(r.yr), int(r.mo)): (float(r.total), int(r.count)) for r in rows}

        labels = [f"{MONTH_NAMES[m]}/{str(y)[2:]}" for y, m in months]
        revenues = [row_map.get((y, m), (0.0, 0))[0] for y, m in months]
        counts = [float(row_map.get((y, m), (0.0, 0))[1]) for y, m in months]

        return BarChartData(
            labels=labels,
            series=[
                ChartSeries(name="Ingresos ($)", data=revenues),
                ChartSeries(name="N° ventas", data=counts),
            ],
        )

    def _top_products(self) -> BarChartData:
        """Top 5 products by units sold."""
        rows = (
            self.db.query(
                Product.name,
                func.sum(DetailSale.quantity).label("total_qty"),
                func.sum(DetailSale.total).label("total_revenue"),
            )
            .join(Sale, DetailSale.sale_id == Sale.id)
            .join(DetailRoastedCoffee, DetailSale.detail_roasted_coffee_id == DetailRoastedCoffee.id)
            .join(Product, DetailRoastedCoffee.product_id == Product.id)
            .filter(Sale.status == SaleStatusEnum.completed)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(DetailSale.quantity).desc())
            .limit(5)
            .all()
        )

        labels = [r.name for r in rows] or ["Sin ventas"]
        qty_data = [float(r.total_qty) for r in rows] or [0.0]
        rev_data = [float(r.total_revenue) for r in rows] or [0.0]

        return BarChartData(
            labels=labels,
            series=[
                ChartSeries(name="Unidades vendidas", data=qty_data),
                ChartSeries(name="Ingresos ($)", data=rev_data),
            ],
        )

    def _inventory_status(self) -> BarChartData:
        """Per-product: total produced vs remaining vs sold."""
        rows = (
            self.db.query(
                Product.name,
                func.sum(DetailRoastedCoffee.quantity).label("total"),
                func.sum(DetailRoastedCoffee.remaining_quantity).label("remaining"),
            )
            .join(Product, DetailRoastedCoffee.product_id == Product.id)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(DetailRoastedCoffee.quantity).desc())
            .limit(8)
            .all()
        )

        labels = [r.name for r in rows] or ["Sin productos"]
        total_data = [float(r.total) for r in rows] or [0.0]
        remaining_data = [float(r.remaining) for r in rows] or [0.0]
        sold_data = [max(0.0, t - rem) for t, rem in zip(total_data, remaining_data)]

        return BarChartData(
            labels=labels,
            series=[
                ChartSeries(name="Total producido", data=total_data),
                ChartSeries(name="Disponible", data=remaining_data),
                ChartSeries(name="Vendido", data=sold_data),
            ],
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_colombian_price(raw: str) -> Optional[float]:
        """Convert '$ 2.320.000,00' → 2320000.0 (dots = thousands, comma = decimal)"""
        try:
            # Remove currency symbol and spaces
            cleaned = re.sub(r"[^\d.,]", "", raw)
            # Remove thousands dots, replace decimal comma
            cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, AttributeError):
            return None
