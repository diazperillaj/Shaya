"""Ventas directas (no de feria): agregaciones, ranking y detalle."""

from app.analytics.base import (
    DateRange,
    add_month_column,
    add_week_column,
    clamp_top,
    df_to_rows,
    num,
    parse_range,
    read_df,
    result,
    ToolError,
)

_LINES_SQL = """
    SELECT s.id            AS venta_id,
           s.sale_date     AS fecha,
           s.status        AS estado,
           d.quantity      AS unidades,
           d.total         AS total_linea,
           pr.id           AS producto_id,
           pr.name         AS producto,
           c.id            AS cliente_id,
           COALESCE(per.full_name, 'Sin cliente') AS cliente
    FROM sales s
    JOIN detail_sales d   ON d.sale_id = s.id
    JOIN detail_roasted_coffees drc ON drc.id = d.detail_roasted_coffee_id
    JOIN products pr      ON pr.id = drc.product_id
    LEFT JOIN customers c ON c.id = s.customer_id
    LEFT JOIN persons per ON per.id = c.person_id
    WHERE (:d0 IS NULL OR s.sale_date >= :d0)
      AND (:d1 IS NULL OR s.sale_date <  :d1)
      AND (:estado IS NULL OR s.status = :estado)
      AND (:producto_id IS NULL OR pr.id = :producto_id)
      AND (:cliente_id IS NULL OR c.id = :cliente_id)
"""

_GROUP_KEYS = {
    "producto": "producto",
    "cliente": "cliente",
    "mes": "mes",
    "semana": "semana",
    "dia": "fecha",
}


def _fetch_lines(rango: DateRange, estado: str, producto_id: int | None, cliente_id: int | None):
    d0, d1 = rango.date_bounds()
    return read_df(
        _LINES_SQL,
        {
            "d0": d0,
            "d1": d1,
            "estado": None if estado == "todas" else estado,
            "producto_id": producto_id,
            "cliente_id": cliente_id,
        },
    )


def consultar_ventas(
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    agrupar_por: str = "ninguno",
    metrica: str = "total",
    filtro_producto_id: int | None = None,
    filtro_cliente_id: int | None = None,
    estado: str = "completed",
    orden: str = "desc",
    top: int = 10,
) -> dict:
    rango = parse_range(fecha_inicio, fecha_fin)
    top = clamp_top(top)
    advertencias = list(rango.warnings)

    # Las ventas directas se registran por FECHA (sin hora)
    if rango.has_time:
        advertencias.append(
            "Las ventas directas registran solo la fecha (sin hora): "
            "el rango se aplicó por días completos."
        )

    df = _fetch_lines(rango, estado, filtro_producto_id, filtro_cliente_id)

    resumen = {
        "periodo": rango.label,
        "estado": estado,
        "total": num(df["total_linea"].sum()),
        "unidades": int(df["unidades"].sum()) if not df.empty else 0,
        "num_ventas": int(df["venta_id"].nunique()),
    }

    if df.empty:
        return result(resumen, advertencias=advertencias + ["Sin ventas en ese rango/filtro."])

    if agrupar_por == "ninguno":
        return result(resumen, advertencias=advertencias or None)

    if agrupar_por == "mes":
        df = add_month_column(df, "fecha")
    elif agrupar_por == "semana":
        df = add_week_column(df, "fecha")

    key = _GROUP_KEYS[agrupar_por]
    grouped = (
        df.groupby(key)
        .agg(
            total=("total_linea", "sum"),
            unidades=("unidades", "sum"),
            num_ventas=("venta_id", "nunique"),
        )
        .reset_index()
    )
    grouped["ticket_promedio"] = grouped["total"] / grouped["num_ventas"]

    sort_col = metrica if metrica in grouped.columns else "total"
    grouped = grouped.sort_values(sort_col, ascending=(orden == "asc"))

    filas, truncado = df_to_rows(grouped, top)
    if truncado:
        advertencias.append(f"Mostrando solo top {top} de {len(grouped)} grupos.")
    return result(resumen, filas=filas, advertencias=advertencias or None)


def detalle_venta(venta_id: int) -> dict:
    header = read_df(
        """
        SELECT s.id, s.sale_date AS fecha, s.status AS estado,
               s.subtotal, s.iva, s.total, s.observations AS observaciones,
               COALESCE(per.full_name, 'Sin cliente') AS cliente,
               pm.name AS metodo_pago
        FROM sales s
        LEFT JOIN customers c ON c.id = s.customer_id
        LEFT JOIN persons per ON per.id = c.person_id
        LEFT JOIN payment_methods pm ON pm.id = s.payment_method_id
        WHERE s.id = :id
        """,
        {"id": venta_id},
    )
    if header.empty:
        raise ToolError(f"La venta #{venta_id} no existe.")

    lines = read_df(
        """
        SELECT pr.name AS producto, d.detail_roasted_coffee_id AS lote_id,
               d.quantity AS unidades, d.unit_value AS valor_unitario, d.total
        FROM detail_sales d
        JOIN detail_roasted_coffees drc ON drc.id = d.detail_roasted_coffee_id
        JOIN products pr ON pr.id = drc.product_id
        WHERE d.sale_id = :id
        """,
        {"id": venta_id},
    )

    h = header.iloc[0]
    filas, _ = df_to_rows(lines, 50)
    return result(
        {
            "venta_id": int(h.id),
            "fecha": str(h.fecha),
            "estado": h.estado,
            "cliente": h.cliente,
            "metodo_pago": h.metodo_pago,
            "subtotal": num(h.subtotal),
            "iva": num(h.iva),
            "total": num(h.total),
            "observaciones": h.observaciones,
        },
        filas=filas,
    )
