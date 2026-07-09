"""Perfil de compras de un cliente: qué compra, cuánto, con qué frecuencia."""

from app.analytics.base import ToolError, df_to_rows, num, read_df, result


def perfil_cliente(cliente_id: int, top: int = 15) -> dict:
    header = read_df(
        """
        SELECT c.id, per.full_name AS nombre, c."customerType" AS tipo, c.city AS ciudad
        FROM customers c JOIN persons per ON per.id = c.person_id
        WHERE c.id = :id
        """,
        {"id": cliente_id},
    )
    if header.empty:
        raise ToolError(
            f"El cliente #{cliente_id} no existe. Usa resolver_entidad para buscarlo por nombre."
        )

    compras = read_df(
        """
        SELECT s.id AS venta_id, s.sale_date AS fecha,
               pr.name AS producto, d.quantity AS unidades, d.total AS total
        FROM sales s
        JOIN detail_sales d ON d.sale_id = s.id
        JOIN detail_roasted_coffees drc ON drc.id = d.detail_roasted_coffee_id
        JOIN products pr ON pr.id = drc.product_id
        WHERE s.customer_id = :id AND s.status = 'completed'
        """,
        {"id": cliente_id},
    )

    h = header.iloc[0]
    if compras.empty:
        return result(
            {"cliente_id": int(h.id), "nombre": h.nombre, "ciudad": h.ciudad, "num_ventas": 0},
            advertencias=["Este cliente no tiene compras completadas registradas."],
        )

    por_producto = (
        compras.groupby("producto")
        .agg(
            unidades=("unidades", "sum"),
            total=("total", "sum"),
            num_compras=("venta_id", "nunique"),
            ultima_compra=("fecha", "max"),
        )
        .reset_index()
        .sort_values("unidades", ascending=False)
    )
    total_general = compras["total"].sum()
    por_producto["pct_del_total"] = (por_producto["total"] / total_general * 100).round(1)

    filas, _ = df_to_rows(por_producto, top)
    num_ventas = int(compras["venta_id"].nunique())

    return result(
        {
            "cliente_id": int(h.id),
            "nombre": h.nombre,
            "tipo": h.tipo,
            "ciudad": h.ciudad,
            "total_comprado": num(total_general),
            "num_ventas": num_ventas,
            "ticket_promedio": num(float(total_general) / num_ventas),
            "primera_compra": str(compras["fecha"].min()),
            "ultima_compra": str(compras["fecha"].max()),
            "producto_favorito": por_producto.iloc[0]["producto"],
        },
        filas=filas,
    )
