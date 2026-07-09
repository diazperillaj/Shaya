"""Gastos generales de la empresa (no ligados a proceso ni feria)."""

from app.analytics.base import (
    add_month_column,
    clamp_top,
    df_to_rows,
    num,
    parse_range,
    read_df,
    result,
)

_SQL = """
    SELECT e.id, e.expense_date AS fecha, e.amount AS monto,
           e.description AS descripcion,
           cat.name AS categoria,
           COALESCE(pm.name, 'Sin método') AS metodo_pago
    FROM general_expenses e
    JOIN expense_categories cat ON cat.id = e.category_id
    LEFT JOIN payment_methods pm ON pm.id = e.payment_method_id
    WHERE (:d0 IS NULL OR e.expense_date >= :d0)
      AND (:d1 IS NULL OR e.expense_date <  :d1)
      AND (:categoria IS NULL OR cat.name ILIKE :categoria)
"""


def consultar_gastos_generales(
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    agrupar_por: str = "categoria",
    filtro_categoria: str | None = None,
    orden: str = "desc",
    top: int = 15,
) -> dict:
    rango = parse_range(fecha_inicio, fecha_fin)
    top = clamp_top(top)
    d0, d1 = rango.date_bounds()
    df = read_df(
        _SQL,
        {"d0": d0, "d1": d1, "categoria": f"%{filtro_categoria}%" if filtro_categoria else None},
    )

    resumen = {
        "periodo": rango.label,
        "total": num(df["monto"].sum()) if not df.empty else 0,
        "num_gastos": len(df),
    }
    if df.empty:
        return result(resumen, advertencias=["Sin gastos en ese rango/filtro."])

    if agrupar_por == "ninguno":
        filas, truncado = df_to_rows(
            df.sort_values("monto", ascending=(orden == "asc")), top
        )
        adv = [f"Mostrando {top} de {len(df)} gastos."] if truncado else None
        return result(resumen, filas=filas, advertencias=adv)

    if agrupar_por == "mes":
        df = add_month_column(df, "fecha")
    key = {"categoria": "categoria", "metodo_pago": "metodo_pago", "mes": "mes"}[agrupar_por]

    grouped = (
        df.groupby(key)
        .agg(total=("monto", "sum"), num_gastos=("id", "count"))
        .reset_index()
        .sort_values("total", ascending=(orden == "asc"))
    )
    grouped["pct_del_total"] = (
        grouped["total"].astype(float) / float(df["monto"].sum()) * 100
    ).round(1)

    filas, _ = df_to_rows(grouped, top)
    return result(resumen, filas=filas)
