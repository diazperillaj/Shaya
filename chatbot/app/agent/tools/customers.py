from app.agent.registry import ToolSpec
from app.agent.tools._shared import TOP, params
from app.analytics.customers import perfil_cliente

TOOLS = [
    ToolSpec(
        name="perfil_cliente",
        description=(
            "Perfil de compras de UN cliente: qué productos compra (con unidades, "
            "frecuencia y % del total), ticket promedio, primera/última compra y "
            "producto favorito. Úsala para preguntas de gustos o hábitos "
            "('¿a Lina le gusta el café en grano?', '¿qué compra el cliente 7?'). "
            "Si solo tienes el nombre, resuelve primero con resolver_entidad."
        ),
        parameters=params(
            {
                "cliente_id": {"type": "integer", "description": "Id del cliente."},
                "top": TOP,
            },
            required=["cliente_id"],
        ),
        executor=perfil_cliente,
        label="Analizando compras del cliente…",
    ),
]
