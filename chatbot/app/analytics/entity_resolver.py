"""
resolver_entidad: nombres en lenguaje natural → IDs canónicos.

Con el volumen actual (decenas de registros por tipo) se traen los candidatos
del tipo y el fuzzy match se hace en Python (difflib + normalización de
acentos). Si el catálogo crece, el primer filtro pasa a ILIKE/pg_trgm en SQL
sin cambiar el contrato.
"""

import unicodedata
from difflib import SequenceMatcher

from app.analytics.base import read_df, result

_QUERIES: dict[str, str] = {
    "cliente": """
        SELECT c.id, p.full_name AS nombre,
               c.city AS extra
        FROM customers c JOIN persons p ON p.id = c.person_id
    """,
    "caficultor": """
        SELECT f.id, p.full_name AS nombre,
               f.farm_name || ' — ' || f.municipality AS extra
        FROM farmers f JOIN persons p ON p.id = f.person_id
    """,
    "producto": """
        SELECT id, name AS nombre,
               CASE WHEN active THEN 'activo' ELSE 'inactivo' END AS extra
        FROM products
    """,
    "feria": """
        SELECT id, name AS nombre,
               COALESCE(location, '') || ' · ' || TO_CHAR(start_datetime, 'YYYY-MM-DD') AS extra
        FROM fairs
    """,
    "proceso": """
        SELECT id, invoice_number AS nombre,
               TO_CHAR(process_date, 'YYYY-MM-DD') AS extra
        FROM processes
    """,
    "lote": """
        SELECT drc.id, pr.name AS nombre,
               'lote #' || drc.id || ' · quedan ' || drc.remaining_quantity AS extra
        FROM detail_roasted_coffees drc JOIN products pr ON pr.id = drc.product_id
    """,
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower().strip())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def _score(query: str, candidate: str) -> float:
    q, c = _normalize(query), _normalize(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    if q in c or c in q:
        return 0.9
    ratio = SequenceMatcher(None, q, c).ratio()
    # Mejor token individual: "lina" debe matchear "Lina María Pérez"
    best_token = max(
        (SequenceMatcher(None, q, tok).ratio() for tok in c.split()), default=0.0
    )
    return max(ratio, best_token)


def resolver_entidad(tipo: str, texto: str, limite: int = 5) -> dict:
    df = read_df(_QUERIES[tipo])

    if df.empty:
        return result(
            {"tipo": tipo, "busqueda": texto, "encontrados": 0},
            advertencias=[f"No hay registros de tipo '{tipo}' en el sistema."],
        )

    df["score"] = df["nombre"].astype(str).map(lambda n: _score(texto, n))
    df = df.sort_values("score", ascending=False)
    matches = df[df["score"] >= 0.5].head(limite)

    if matches.empty:
        cercanos = df.head(3)["nombre"].tolist()
        return result(
            {"tipo": tipo, "busqueda": texto, "encontrados": 0},
            advertencias=[
                f"Ningún {tipo} coincide con '{texto}'. Nombres existentes más cercanos: "
                + ", ".join(cercanos)
            ],
        )

    filas = [
        {
            "id": int(row.id),
            "nombre": row.nombre,
            "detalle": row.extra,
            "score": round(float(row.score), 2),
        }
        for row in matches.itertuples()
    ]

    # Coincidencia única y clara → el modelo puede usar el id sin preguntar
    unico = len(filas) == 1 or (
        filas[0]["score"] >= 0.85 and (len(filas) == 1 or filas[0]["score"] - filas[1]["score"] >= 0.15)
    )

    return result(
        {
            "tipo": tipo,
            "busqueda": texto,
            "encontrados": len(filas),
            "coincidencia_unica": unico,
        },
        filas=filas,
    )
