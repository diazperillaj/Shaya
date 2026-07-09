from app.agent.registry import ToolSpec
from app.agent.tools._shared import FECHA, TOP, params
from app.analytics.inventory import estado_inventario, movimientos_maquilado

TOOLS = [
    ToolSpec(
        name="estado_inventario",
        description=(
            "Fotografía ACTUAL del stock: café tostado (unidades por producto o por "
            "lote) y/o pergamino (kg por lote de compra). Úsala para '¿cuánto queda "
            "de…?', '¿qué está por agotarse?'. Para el histórico de movimientos usa "
            "movimientos_maquilado."
        ),
        parameters=params(
            {
                "tipo": {
                    "type": "string",
                    "enum": ["tostado", "pergamino", "ambos"],
                    "description": "Default: tostado (producto terminado).",
                },
                "filtro_producto_id": {"type": "integer", "description": "Limitar a un producto."},
                "agrupar_por": {
                    "type": "string",
                    "enum": ["producto", "lote"],
                    "description": "Default: producto. 'lote' muestra cada lote con su id.",
                },
                "solo_bajo_stock": {
                    "type": "boolean",
                    "description": "true = solo lo que está en o bajo el umbral.",
                },
                "umbral_bajo_stock": {"type": "integer", "minimum": 1, "description": "Default: 10."},
                "top": TOP,
            }
        ),
        executor=estado_inventario,
        label="Revisando el inventario…",
    ),
    ToolSpec(
        name="movimientos_maquilado",
        description=(
            "Historial de movimientos del inventario de maquilado (café tostado): "
            "salidas, entradas y reempaques, con las líneas de cada movimiento. "
            "Úsala para '¿el lote 5 tuvo reempaque?' (lote_id=5, tipo='reempaque') o "
            "'¿qué salidas hubo esta semana?'. 'inventario de maquilado N' = lote_id N."
        ),
        parameters=params(
            {
                "lote_id": {
                    "type": "integer",
                    "description": "Id del lote (detail_roasted_coffee). Omitir = todos.",
                },
                "tipo": {
                    "type": "string",
                    "enum": ["salida", "entrada", "reempaque", "todos"],
                    "description": "Default: todos.",
                },
                "fecha_inicio": FECHA,
                "fecha_fin": FECHA,
                "top": TOP,
            }
        ),
        executor=movimientos_maquilado,
        label="Rastreando movimientos de maquilado…",
    ),
]
