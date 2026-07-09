from app.agent.registry import ToolSpec
from app.agent.tools._shared import FECHA, ORDEN, TOP, params
from app.analytics.purchases import consultar_compras_pergamino

TOOLS = [
    ToolSpec(
        name="consultar_compras_pergamino",
        description=(
            "Compras de café pergamino a caficultores: kilos, costo total y precio "
            "promedio por kg; agregables por caficultor, variedad o mes. Úsala para "
            "'¿a quién le compramos más café?', '¿a qué precio compramos?'."
        ),
        parameters=params(
            {
                "fecha_inicio": FECHA,
                "fecha_fin": FECHA,
                "agrupar_por": {
                    "type": "string",
                    "enum": ["caficultor", "variedad", "mes", "ninguno"],
                    "description": "'ninguno' lista compras individuales. Default: caficultor.",
                },
                "filtro_caficultor_id": {"type": "integer", "description": "Limitar a un caficultor."},
                "orden": ORDEN,
                "top": TOP,
            }
        ),
        executor=consultar_compras_pergamino,
        label="Consultando compras de pergamino…",
    ),
]
