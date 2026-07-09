"""Compras de café pergamino a caficultores."""

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
    SELECT par.id, par.purchase_date AS fecha,
           par.variety AS variedad,
           par.initial_quantity AS kg,
           par.remaining_quantity AS kg_restantes,
           par.purchase_price AS costo_total_lote,
           per.full_name AS caficultor,
           f.farm_name AS finca
    FROM parchments par
    JOIN farmers f ON f.id = par.farmer_id
    JOIN persons per ON per.id = f.person_id
    WHERE (:d0 IS NULL OR par.purchase_date >= :d0)
      AND (:d1 IS NULL OR par.purchase_date <  :d1)
      AND (:farmer_id IS NULL OR f.id = :farmer_id)
"""


def consultar_compras_pergamino(
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    agrupar_por: str = "caficultor",
    filtro_caficultor_id: int | None = None,
    orden: str = "desc",
    top: int = 10,
) -> dict:
    rango = parse_range(fecha_inicio, fecha_fin)
    top = clamp_top(top)
    d0, d1 = rango.date_bounds()
    df = read_df(_SQL, {"d0": d0, "d1": d1, "farmer_id": filtro_caficultor_id})

    if df.empty:
        return result(
            {"periodo": rango.label, "num_compras": 0},
            advertencias=["Sin compras de pergamino en ese rango/filtro."],
        )

    kg_total = float(df["kg"].sum())
    costo_total = float(df["costo_total_lote"].sum())
    advertencias = []
    # Lotes históricos importados del Excel pueden tener costo 0
    sin_costo = df[df["costo_total_lote"] == 0]
    if not sin_costo.empty:
        advertencias.append(
            f"{len(sin_costo)} compra(s) importadas del histórico tienen costo $0: "
            "el precio promedio real puede ser mayor."
        )

    resumen = {
        "periodo": rango.label,
        "num_compras": len(df),
        "kg_comprados": num(kg_total),
        "costo_total": num(costo_total),
        "precio_promedio_kg": num(costo_total / kg_total) if kg_total else None,
    }

    if agrupar_por == "ninguno":
        filas, _ = df_to_rows(df.sort_values("fecha", ascending=(orden == "asc")), top)
        return result(resumen, filas=filas, advertencias=advertencias or None)

    if agrupar_por == "mes":
        df = add_month_column(df, "fecha")
    key = {"caficultor": "caficultor", "variedad": "variedad", "mes": "mes"}[agrupar_por]

    grouped = (
        df.groupby(key)
        .agg(
            kg=("kg", "sum"),
            costo_total=("costo_total_lote", "sum"),
            num_compras=("id", "count"),
        )
        .reset_index()
    )
    grouped["precio_promedio_kg"] = (
        grouped["costo_total"].astype(float) / grouped["kg"].astype(float)
    ).round(2)
    grouped = grouped.sort_values("kg", ascending=(orden == "asc"))

    filas, _ = df_to_rows(grouped, top)
    return result(resumen, filas=filas, advertencias=advertencias or None)
