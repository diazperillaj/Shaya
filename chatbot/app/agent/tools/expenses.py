from app.agent.registry import ToolSpec
from app.agent.tools._shared import FECHA, ORDEN, TOP, params
from app.analytics.expenses import consultar_gastos_generales

TOOLS = [
    ToolSpec(
        name="consultar_gastos_generales",
        description=(
            "Gastos generales de la empresa (nómina, publicidad, transporte…), NO los "
            "gastos de procesos ni de ferias. Agregables por categoría, método de pago "
            "o mes. Úsala para '¿cuánto gastamos en…?', '¿qué pagamos con Nequi?'."
        ),
        parameters=params(
            {
                "fecha_inicio": FECHA,
                "fecha_fin": FECHA,
                "agrupar_por": {
                    "type": "string",
                    "enum": ["categoria", "metodo_pago", "mes", "ninguno"],
                    "description": "'ninguno' lista gastos individuales. Default: categoria.",
                },
                "filtro_categoria": {
                    "type": "string",
                    "description": "Nombre (o parte) de la categoría, ej. 'nomina'.",
                },
                "orden": ORDEN,
                "top": TOP,
            }
        ),
        executor=consultar_gastos_generales,
        label="Sumando gastos generales…",
    ),
]
