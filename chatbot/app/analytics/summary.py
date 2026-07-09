"""Resumen ejecutivo multi-dominio: '¿cómo va el negocio?'."""

from datetime import datetime, timedelta

from app.analytics.base import BOGOTA, now_bogota, num, read_df, result


def _period_bounds(periodo: str) -> tuple[datetime | None, datetime | None, str]:
    now = now_bogota()
    if periodo == "mes_actual":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, None, f"mes actual ({start:%Y-%m})"
    if periodo == "trimestre_actual":
        month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, None, f"trimestre actual (desde {start:%Y-%m-%d})"
    if periodo == "año_actual":
        start = datetime(now.year, 1, 1, tzinfo=BOGOTA)
        return start, None, f"año {now.year}"
    return None, None, "todo el histórico"


def resumen_ejecutivo(periodo: str = "mes_actual") -> dict:
    start, end, label = _period_bounds(periodo)
    d0 = start.date() if start else None
    d1 = (end.date() + timedelta(days=1)) if end else None
    params = {"d0": d0, "d1": d1}

    ventas = read_df(
        """
        SELECT COALESCE(SUM(total), 0) AS total, COUNT(*) AS num
        FROM sales
        WHERE status = 'completed'
          AND (:d0 IS NULL OR sale_date >= :d0)
          AND (:d1 IS NULL OR sale_date < :d1)
        """,
        params,
    ).iloc[0]

    top_producto = read_df(
        """
        SELECT pr.name AS producto, SUM(d.quantity) AS unidades, SUM(d.total) AS total
        FROM sales s
        JOIN detail_sales d ON d.sale_id = s.id
        JOIN detail_roasted_coffees drc ON drc.id = d.detail_roasted_coffee_id
        JOIN products pr ON pr.id = drc.product_id
        WHERE s.status = 'completed'
          AND (:d0 IS NULL OR s.sale_date >= :d0)
          AND (:d1 IS NULL OR s.sale_date < :d1)
        GROUP BY pr.name ORDER BY SUM(d.quantity) DESC LIMIT 1
        """,
        params,
    )

    stock = read_df(
        """
        SELECT
          (SELECT COALESCE(SUM(remaining_quantity), 0) FROM detail_roasted_coffees) AS tostado_unidades,
          (SELECT COALESCE(SUM(remaining_quantity), 0) FROM parchments) AS pergamino_kg
        """
    ).iloc[0]

    procesos = read_df(
        """
        SELECT COUNT(*) AS num,
               COALESCE(SUM(parchment_kg), 0) AS kg_procesados,
               COALESCE(SUM(resultant_kg), 0) AS kg_resultantes
        FROM processes
        WHERE (:d0 IS NULL OR process_date >= :d0)
          AND (:d1 IS NULL OR process_date < :d1)
        """,
        params,
    ).iloc[0]

    gastos = read_df(
        """
        SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS num
        FROM general_expenses
        WHERE (:d0 IS NULL OR expense_date >= :d0)
          AND (:d1 IS NULL OR expense_date < :d1)
        """,
        params,
    ).iloc[0]

    clientes_activos = read_df(
        """
        SELECT COUNT(DISTINCT customer_id) AS n
        FROM sales
        WHERE customer_id IS NOT NULL AND status = 'completed'
          AND (:d0 IS NULL OR sale_date >= :d0)
          AND (:d1 IS NULL OR sale_date < :d1)
        """,
        params,
    ).iloc[0]

    kg_proc = float(procesos["kg_procesados"])
    resumen = {
        "periodo": label,
        "ventas_total": num(ventas["total"]),
        "num_ventas": int(ventas["num"]),
        "ticket_promedio": num(float(ventas["total"]) / int(ventas["num"])) if int(ventas["num"]) else None,
        "producto_mas_vendido": (
            {
                "producto": top_producto.iloc[0]["producto"],
                "unidades": int(top_producto.iloc[0]["unidades"]),
                "total": num(top_producto.iloc[0]["total"]),
            }
            if not top_producto.empty
            else None
        ),
        "stock_tostado_unidades": int(stock["tostado_unidades"]),
        "stock_pergamino_kg": num(stock["pergamino_kg"]),
        "procesos": {
            "num": int(procesos["num"]),
            "kg_procesados": num(kg_proc),
            "rendimiento_pct": num(float(procesos["kg_resultantes"]) / kg_proc * 100, 1) if kg_proc else None,
        },
        "gastos_generales_total": num(gastos["total"]),
        "clientes_con_compra": int(clientes_activos["n"]),
    }

    advertencias = []
    if int(ventas["num"]) == 0:
        advertencias.append("No hay ventas completadas en el periodo.")
    return result(resumen, advertencias=advertencias or None)
