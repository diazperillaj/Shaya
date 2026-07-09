"""Procesos de maquila/tostado: kilos, rendimiento y costo de maquila."""

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
    SELECT p.id AS proceso_id, p.invoice_number AS factura,
           p.process_date AS fecha,
           p.parchment_kg AS kg_procesados,
           p.resultant_kg AS kg_resultantes,
           p.yield_percentage AS rendimiento,
           p.total AS costo_maquila,
           par.variety AS variedad,
           per.full_name AS caficultor
    FROM processes p
    JOIN parchments par ON par.id = p.parchment_id
    JOIN farmers f ON f.id = par.farmer_id
    JOIN persons per ON per.id = f.person_id
    WHERE (:d0 IS NULL OR p.process_date >= :d0)
      AND (:d1 IS NULL OR p.process_date <  :d1)
"""


def consultar_procesos(
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    agrupar_por: str = "ninguno",
    orden: str = "desc",
    top: int = 10,
) -> dict:
    rango = parse_range(fecha_inicio, fecha_fin)
    top = clamp_top(top)
    d0, d1 = rango.date_bounds()
    df = read_df(_SQL, {"d0": d0, "d1": d1})

    if df.empty:
        return result(
            {"periodo": rango.label, "num_procesos": 0},
            advertencias=["No hay procesos en ese rango."],
        )

    kg_proc = float(df["kg_procesados"].sum())
    kg_res = float(df["kg_resultantes"].sum())
    resumen = {
        "periodo": rango.label,
        "num_procesos": len(df),
        "kg_procesados": num(kg_proc),
        "kg_resultantes": num(kg_res),
        # Rendimiento ponderado por kilos, no promedio simple de porcentajes
        "rendimiento_promedio_pct": num(kg_res / kg_proc * 100, 1) if kg_proc else None,
        "costo_maquila_total": num(df["costo_maquila"].sum()),
    }

    if agrupar_por == "ninguno":
        filas, truncado = df_to_rows(df.sort_values("fecha", ascending=(orden == "asc")), top)
        adv = [f"Mostrando {top} de {len(df)} procesos."] if truncado else None
        return result(resumen, filas=filas, advertencias=adv)

    if agrupar_por == "mes":
        df = add_month_column(df, "fecha")
    key = {"mes": "mes", "caficultor": "caficultor", "variedad": "variedad"}[agrupar_por]

    grouped = (
        df.groupby(key)
        .agg(
            num_procesos=("proceso_id", "count"),
            kg_procesados=("kg_procesados", "sum"),
            kg_resultantes=("kg_resultantes", "sum"),
            costo_maquila=("costo_maquila", "sum"),
        )
        .reset_index()
    )
    grouped["rendimiento_pct"] = (
        grouped["kg_resultantes"].astype(float) / grouped["kg_procesados"].astype(float) * 100
    ).round(1)
    grouped = grouped.sort_values("kg_procesados", ascending=(orden == "asc"))

    filas, _ = df_to_rows(grouped, top)
    return result(resumen, filas=filas)
