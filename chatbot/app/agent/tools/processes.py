from app.agent.registry import ToolSpec
from app.agent.tools._shared import FECHA, ORDEN, TOP, params
from app.analytics.processes import consultar_procesos

TOOLS = [
    ToolSpec(
        name="consultar_procesos",
        description=(
            "Procesos de maquila/tostado: kilos procesados y resultantes, rendimiento "
            "(%) y costo de maquila; agregable por mes, caficultor o variedad. Úsala "
            "para '¿cuántos kilos tostamos?', '¿qué rendimiento tuvimos?'. "
            "'proceso N' = id del proceso."
        ),
        parameters=params(
            {
                "fecha_inicio": FECHA,
                "fecha_fin": FECHA,
                "agrupar_por": {
                    "type": "string",
                    "enum": ["mes", "caficultor", "variedad", "ninguno"],
                    "description": "'ninguno' lista procesos individuales. Default: ninguno.",
                },
                "orden": ORDEN,
                "top": TOP,
            }
        ),
        executor=consultar_procesos,
        label="Consultando procesos de maquila…",
    ),
]
