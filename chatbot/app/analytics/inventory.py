"""Inventario: stock de tostado/pergamino y movimientos de maquilado."""

import pandas as pd

from app.analytics.base import (
    clamp_top,
    df_to_rows,
    num,
    parse_range,
    read_df,
    result,
    ToolError,
)


def estado_inventario(
    tipo: str = "tostado",
    filtro_producto_id: int | None = None,
    agrupar_por: str = "producto",
    solo_bajo_stock: bool = False,
    umbral_bajo_stock: int = 10,
    top: int = 20,
) -> dict:
    top = clamp_top(top)
    partes: dict = {}
    filas: list[dict] = []
    advertencias: list[str] = []

    if tipo in ("tostado", "ambos"):
        df = read_df(
            """
            SELECT drc.id AS lote_id, pr.name AS producto,
                   drc.quantity AS unidades_iniciales,
                   drc.remaining_quantity AS unidades_restantes,
                   drc.unit_cost AS costo_unitario,
                   rc.process_id AS proceso_id
            FROM detail_roasted_coffees drc
            JOIN products pr ON pr.id = drc.product_id
            JOIN roasted_coffees rc ON rc.id = drc.roasted_coffee_id
            WHERE (:producto_id IS NULL OR pr.id = :producto_id)
            """,
            {"producto_id": filtro_producto_id},
        )
        partes["tostado_unidades_restantes"] = int(df["unidades_restantes"].sum()) if not df.empty else 0
        partes["tostado_num_lotes"] = len(df)

        if agrupar_por == "producto":
            agg = (
                df.groupby("producto")
                .agg(
                    unidades_restantes=("unidades_restantes", "sum"),
                    num_lotes=("lote_id", "count"),
                )
                .reset_index()
                .sort_values("unidades_restantes", ascending=False)
            )
        else:  # lote
            agg = df.sort_values("unidades_restantes", ascending=False)

        if solo_bajo_stock:
            agg = agg[agg["unidades_restantes"] <= umbral_bajo_stock]
            partes["umbral_bajo_stock"] = umbral_bajo_stock

        rows, truncado = df_to_rows(agg, top)
        filas.extend(rows)
        if truncado:
            advertencias.append(f"Tostado: mostrando top {top} de {len(agg)}.")

    if tipo in ("pergamino", "ambos"):
        dfp = read_df(
            """
            SELECT par.id AS pergamino_id, per.full_name AS caficultor,
                   par.variety AS variedad,
                   par.initial_quantity AS kg_iniciales,
                   par.remaining_quantity AS kg_restantes,
                   par.purchase_date AS fecha_compra
            FROM parchments par
            JOIN farmers f ON f.id = par.farmer_id
            JOIN persons per ON per.id = f.person_id
            ORDER BY par.remaining_quantity DESC
            """
        )
        partes["pergamino_kg_restantes"] = num(dfp["kg_restantes"].sum()) if not dfp.empty else 0
        partes["pergamino_num_lotes"] = len(dfp)
        if tipo == "pergamino":
            rows, _ = df_to_rows(dfp, top)
            filas.extend(rows)

    if not filas and solo_bajo_stock:
        advertencias.append("Ningún producto está por debajo del umbral de bajo stock.")

    return result(partes, filas=filas or None, advertencias=advertencias or None)


def movimientos_maquilado(
    lote_id: int | None = None,
    tipo: str = "todos",
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    top: int = 15,
) -> dict:
    """
    Movimientos de inventario de maquilado. El tipo NO está almacenado:
    se infiere de las líneas del movimiento —
      solo salidas → 'salida' · solo entradas → 'entrada' ·
      salidas Y entradas en el mismo movimiento → 'reempaque'.
    """
    top = clamp_top(top)
    rango = parse_range(fecha_inicio, fecha_fin)

    if lote_id is not None:
        existe = read_df(
            "SELECT id FROM detail_roasted_coffees WHERE id = :id", {"id": lote_id}
        )
        if existe.empty:
            raise ToolError(
                f"El lote de maquilado #{lote_id} no existe. "
                "Usa estado_inventario(tipo='tostado', agrupar_por='lote') para ver los lotes."
            )

    df = read_df(
        """
        SELECT m.id AS movimiento_id, m.movement_date AS fecha,
               m.observations AS observaciones,
               det.detail_roasted_coffee_id AS lote_id,
               pr.name AS producto,
               det.quantity AS unidades,
               det.direction::text AS direccion,
               det.created_lot AS creo_lote
        FROM roasted_movements m
        JOIN roasted_movement_details det ON det.movement_id = m.id
        JOIN detail_roasted_coffees drc ON drc.id = det.detail_roasted_coffee_id
        JOIN products pr ON pr.id = drc.product_id
        WHERE m.id IN (
            SELECT movement_id FROM roasted_movement_details
            WHERE (:lote_id IS NULL OR detail_roasted_coffee_id = :lote_id)
        )
          AND (:t0 IS NULL OR m.movement_date >= :t0)
          AND (:t1 IS NULL OR m.movement_date <  :t1)
        ORDER BY m.movement_date DESC, m.id DESC
        """,
        {"lote_id": lote_id, "t0": rango.start, "t1": rango.end},
    )

    if df.empty:
        objeto = f"el lote #{lote_id}" if lote_id else "ese rango"
        return result(
            {"periodo": rango.label, "movimientos": 0},
            advertencias=[f"No hay movimientos de maquilado para {objeto}."],
        )

    def _clasificar(direcciones: pd.Series) -> str:
        tiene_salida = (direcciones == "exit").any()
        tiene_entrada = (direcciones == "entry").any()
        if tiene_salida and tiene_entrada:
            return "reempaque"
        return "salida" if tiene_salida else "entrada"

    tipos = df.groupby("movimiento_id")["direccion"].apply(_clasificar).rename("tipo")
    df = df.merge(tipos, on="movimiento_id")

    if tipo != "todos":
        df = df[df["tipo"] == tipo]
        if df.empty:
            objeto = f"el lote #{lote_id}" if lote_id else "ese rango"
            return result(
                {"periodo": rango.label, "movimientos": 0, "tipo_filtrado": tipo},
                advertencias=[f"No hay movimientos de tipo '{tipo}' para {objeto}."],
            )

    filas = []
    for mov_id, grupo in df.groupby("movimiento_id", sort=False):
        primero = grupo.iloc[0]
        filas.append(
            {
                "movimiento_id": int(mov_id),
                "fecha": str(primero.fecha)[:19],
                "tipo": primero.tipo,
                "lineas": [
                    {
                        "lote_id": int(l.lote_id),
                        "producto": l.producto,
                        "direccion": "entrada" if l.direccion == "entry" else "salida",
                        "unidades": int(l.unidades),
                        "creo_lote": bool(l.creo_lote),
                    }
                    for l in grupo.itertuples()
                ],
                "observaciones": primero.observaciones,
            }
        )
        if len(filas) >= top:
            break

    conteo = df.drop_duplicates("movimiento_id")["tipo"].value_counts().to_dict()
    return result(
        {
            "periodo": rango.label,
            "lote_filtrado": lote_id,
            "movimientos": int(df["movimiento_id"].nunique()),
            "por_tipo": conteo,
        },
        filas=filas,
    )
