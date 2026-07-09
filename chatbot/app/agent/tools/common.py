from app.agent.registry import ToolSpec
from app.agent.tools._shared import params
from app.analytics.entity_resolver import resolver_entidad
from app.analytics.summary import resumen_ejecutivo

TOOLS = [
    ToolSpec(
        name="resolver_entidad",
        description=(
            "Convierte un NOMBRE mencionado por el usuario en su ID. Úsala SIEMPRE que "
            "el usuario nombre un cliente, producto, caficultor, feria, proceso o lote "
            "por texto ('Lina', 'Bourbon', 'feria del parque') y aún no tengas su id. "
            "NO la uses si el usuario ya dio un número: eso ya es el id. Si devuelve "
            "coincidencia_unica=false, pregunta al usuario cuál de los candidatos es."
        ),
        parameters=params(
            {
                "tipo": {
                    "type": "string",
                    "enum": ["cliente", "caficultor", "producto", "feria", "proceso", "lote"],
                },
                "texto": {"type": "string", "description": "Nombre o parte del nombre a buscar."},
                "limite": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            required=["tipo", "texto"],
        ),
        executor=resolver_entidad,
        label="Buscando en el catálogo…",
    ),
    ToolSpec(
        name="resumen_ejecutivo",
        description=(
            "Panorama general del negocio en un periodo: ventas totales, producto más "
            "vendido, stock, procesos, gastos y clientes activos. Úsala para preguntas "
            "abiertas tipo '¿cómo va el negocio?' o '¿cómo nos fue este mes?'. Para "
            "preguntas específicas usa la tool del dominio, no esta."
        ),
        parameters=params(
            {
                "periodo": {
                    "type": "string",
                    "enum": ["mes_actual", "trimestre_actual", "año_actual", "historico"],
                    "description": "Default: mes_actual.",
                }
            }
        ),
        executor=resumen_ejecutivo,
        label="Armando el panorama del negocio…",
    ),
]
