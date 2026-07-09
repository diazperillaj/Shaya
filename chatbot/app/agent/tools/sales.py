from app.agent.registry import ToolSpec
from app.agent.tools._shared import FECHA, ORDEN, TOP, params
from app.analytics.sales import consultar_ventas, detalle_venta

TOOLS = [
    ToolSpec(
        name="consultar_ventas",
        description=(
            "Ventas DIRECTAS (no de feria): totales, rankings y agrupaciones. Úsala para "
            "'¿cuánto vendimos…?', 'top productos', '¿a quién le vendemos más?'. "
            "Las ventas registran solo FECHA (sin hora). Para el historial de UN cliente "
            "usa perfil_cliente; para una venta puntual usa detalle_venta."
        ),
        parameters=params(
            {
                "fecha_inicio": FECHA,
                "fecha_fin": FECHA,
                "agrupar_por": {
                    "type": "string",
                    "enum": ["producto", "cliente", "mes", "semana", "dia", "ninguno"],
                    "description": "Dimensión del desglose. 'ninguno' = solo totales. Default: ninguno.",
                },
                "metrica": {
                    "type": "string",
                    "enum": ["total", "cantidad", "num_ventas", "ticket_promedio"],
                    "description": "Métrica para ordenar el ranking. Default: total (pesos).",
                },
                "filtro_producto_id": {"type": "integer", "description": "Limitar a un producto."},
                "filtro_cliente_id": {"type": "integer", "description": "Limitar a un cliente."},
                "estado": {
                    "type": "string",
                    "enum": ["completed", "in_progress", "todas"],
                    "description": "Default: completed (ventas cerradas).",
                },
                "orden": ORDEN,
                "top": TOP,
            }
        ),
        executor=consultar_ventas,
        label="Consultando ventas…",
    ),
    ToolSpec(
        name="detalle_venta",
        description=(
            "Detalle completo de UNA venta por su id: cliente, método de pago, líneas "
            "con productos y totales. Úsala para '¿qué llevaba la venta 120?'."
        ),
        parameters=params(
            {"venta_id": {"type": "integer", "description": "Id de la venta."}},
            required=["venta_id"],
        ),
        executor=detalle_venta,
        label="Buscando la venta…",
    ),
]
