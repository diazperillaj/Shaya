# Chatbot Analítico de Shaya — Arquitectura del Microservicio

> **Documento maestro de la implementación.** Guía única para programar el servicio.
> Antecedente conceptual: [`arquitectura-asistente-conversacional.md`](arquitectura-asistente-conversacional.md) (diseño original; su limitación de "no se puede calcular utilidad" quedó resuelta con `unit_cost`). Cuando difieran, **este documento manda**.
>
> Última actualización: 2026-07-08 · Estado: No aprobado para implementación

---

## 0. Decisiones de arquitectura (resumen)

| # | Decisión | Elección | Razón |
|---|---|---|---|
| 1 | Ubicación | **Microservicio independiente** `chatbot/` (puerto **8005**), mismo `docker-compose` | Aprender/practicar microservicios; frontera natural (solo lectura del negocio); si se cae, no afecta ventas/inventario |
| 2 | Dónde vive el análisis de datos | **En el microservicio** (capa `analytics/` con Pandas) — NO en el backend | El LLM y su fuente de datos deben estar juntos: cada turno dispara 1–4 consultas analíticas; hacerlas por HTTP al backend duplicaría latencia y acoplaría los despliegues. El backend queda intacto |
| 3 | Acceso a datos del negocio | Conexión **directa a PostgreSQL con usuario de SOLO LECTURA** (`chatbot_ro`) | Práctico y seguro: imposible escribir el negocio por diseño; el contrato es el esquema de la DB (estable, migrado por Alembic del backend) |
| 4 | Datos propios del chat | Schema **`chat`** en el mismo Postgres, usuario RW propio, **Alembic propio** (`alembic_version` dentro del schema `chat`) | Historial persistente y auditable; migraciones aditivas → deploy sin tocar datos existentes |
| 5 | Memoria conversacional caliente | **Redis** (ventana de mensajes, pizarra de entidades, resumen) con TTL | Armar el contexto de cada turno sin golpear Postgres; Postgres sigue siendo la fuente de verdad (Redis es reconstruible) |
| 6 | Proveedor LLM | **SDK `openai` apuntando a Groq** (API OpenAI-compatible) en desarrollo; intercambiable por `LLM_BASE_URL`/`LLM_MODEL` | Groq: gratis/barato y rápido para iterar. El puerto `LLMClient` permite pasar a OpenAI real u otro proveedor sin tocar el agente |
| 7 | Patrón del agente | **Tool calling iterativo con loop manual** (máx. 7 iteraciones), streaming SSE | El LLM decide qué consultar; nunca ve filas crudas ni genera SQL. Loop manual = control total (límites, persistencia, streaming de pasos) |
| 8 | Alcance | **Cerrado al negocio.** Preguntas fuera de dominio ("¿quién es el presidente?") → rechazo cortés estándar | Guardrail por prompt + sin tools de conocimiento general + validación de salida |
| 9 | Estilo de respuesta | **Breve-moderada y precisa** (3–8 líneas o tabla pequeña), `max_tokens` acotado | Ahorro de tokens sin sacrificar claridad |
| 10 | Tiempo | Zona horaria fija **America/Bogota**; todos los filtros aceptan **fecha y hora** (`YYYY-MM-DDTHH:MM:SS`) | Soportar "de ayer 4pm a hoy 1am" |
| 11 | Frontend | Nueva feature `features/chat/` en la misma SPA, ruta por nginx `location /chat/` → `chatbot:8005` | Un solo punto de entrada (nginx del contenedor web); SSE directo al microservicio |
| 12 | Autenticación | El microservicio **valida la misma cookie JWT** del backend (comparte `SECRET_KEY`) | Sin llamadas de auth entre servicios; el usuario ya logueado usa el chat sin fricción |

---

## 1. Objetivo y preguntas que debe responder

Asistente en español que analiza los datos reales de Shaya con precisión de cifras. Preguntas objetivo (reales, del dueño del producto):

| Pregunta | Qué exige del sistema |
|---|---|
| "¿Cuál es el cliente que más ha comprado y qué productos?" | Ranking de clientes + desglose por producto en una sola respuesta (2 tools encadenadas) |
| "¿Cuáles son las mejores ferias en relación ganancia vs gasto?" | Ganancia real por feria: ingresos − costo de lo vendido (`unit_cost`) − gastos de feria; ratio ganancia/gasto |
| "Para el inventario de maquilado 5, ¿se hizo algún reempaque?" | Entender que "5" es el **id del lote** sin que se lo digan; consultar movimientos tipo reempaque de ese lote |
| "¿A la clienta Lina le gusta el café en grano y por libra?" | Fuzzy match "Lina" → cliente; perfil de compras por producto/presentación (grano/molido, gramaje) |
| "¿A cuántas ferias fuimos en marzo y cómo fue la ganancia por cada una?" | Conteo + ganancia por feria en un rango de fechas |
| "¿Cuánto vendimos de ayer a las 4pm hasta hoy a la 1am?" | Rangos datetime con hora, resueltos contra la fecha/hora actual de Bogotá |
| "¿Cual es el ranking de los productos que mas se venden en todas las ciclovias? ¿Cuales fueron los mas vendidos en las ultimas ciclovias?" | Listar ferias como ciclovia, conteo + ganancia y visibilidad de los productos mas vendidos por cada una, hacer comparacion |

Reglas de comportamiento:

1. **Toda cifra proviene de un resultado de tool.** Prohibido estimar o "recordar".
2. **Fuera del negocio → rechazo estándar:** *"Solo puedo ayudarte con información del negocio de Shaya (ventas, inventario, procesos, ferias, clientes, gastos)."*
3. **Ambigüedad de entidades:** si hay varios candidatos plausibles, pregunta; nunca elige en silencio.
4. **Sin datos ≠ error:** "no hay ferias registradas en marzo" es una respuesta válida y clara.
5. **Respuestas breves-moderadas:** el dato primero, contexto mínimo necesario, sin relleno.

---

## 2. Arquitectura general

```
 Navegador ──▶ [Caddy HTTPS] ──▶ ┌──────────────────────┐
  (React SPA)                    │  nginx (contenedor web)│
                                 └────┬────────────┬─────┘
                          /api/ ──────┘            └────── /chat/  (proxy_buffering off)
                             ▼                        ▼
                      ┌────────────┐          ┌──────────────────┐      ┌─────────────┐
                      │  backend   │          │  chatbot :8005   │─────▶│  Groq API   │
                      │  :8000     │          │  (FastAPI)       │      │ (OpenAI-comp)│
                      │  (negocio) │          │                  │      └─────────────┘
                      └─────┬──────┘          │  agente + tools  │
                            │                 │  analytics/pandas│
                            │ RW (public)     └───┬──────────┬───┘
                            ▼                     │          │
                      ┌────────────────────────┐  │          ▼
                      │ PostgreSQL             │◀─┘    ┌───────────┐
                      │  schema public (negocio)│ RO    │  Redis    │
                      │  schema chat (historial)│ RW    │ (memoria) │
                      └────────────────────────┘       └───────────┘
```

- El **backend no cambia** (salvo nada): el chatbot lee `public.*` con `chatbot_ro` (solo SELECT).
- El **chatbot escribe únicamente** en el schema `chat` y en Redis.
- El frontend habla con el chatbot **directo** vía nginx (`/chat/`), incluida la respuesta SSE.
- El LLM (Groq) solo recibe: system prompt + historial acotado + resultados agregados (nunca filas crudas).

### Flujo de un mensaje (end-to-end)

1. Usuario escribe en `ChatPage` → `POST /chat/api/v1/conversations/{id}/messages` (cookie de sesión incluida).
2. El chatbot valida el JWT de la cookie (mismo `SECRET_KEY` del backend).
3. `MemoryService` arma el contexto desde Redis (ventana + pizarra + resumen); si Redis está frío, lo reconstruye desde Postgres. Maximo 30 historial de mensajes por sesion, de ahi se empieza a usar en forma de cola, el primero en entrar empieza a salir y asi termina con informacion reciente, el redis igual debe tener todo el historial pero solo debe contar los ultimos 30. Esto para ahorrar tokens
4. `AgentLoop` llama al LLM con system prompt (+ fecha/hora actual de Bogotá en el turno) y las definiciones de tools.
5. El LLM pide tools (ej. `resolver_entidad("lina")` → `perfil_cliente(id=7)`); cada una ejecuta SQL filtrado + Pandas y devuelve JSON compacto. Cada paso se emite por SSE (`status`) y se persiste en `chat.messages`.
6. Con los resultados, el LLM redacta la respuesta final → se transmite por SSE token a token.
7. Se persiste el turno completo (mensaje, tool calls, tokens, latencia) en Postgres y se actualizan ventana/pizarra en Redis.

---

## 3. Manejo de datos (decisión clave)

**Todo el análisis vive en el microservicio.** El backend es dueño de la escritura del negocio; el chatbot es un **consumidor de solo lectura** del mismo Postgres:

| Rol de DB | Permisos | Usado por |
|---|---|---|
| `shaya` (existente) | RW sobre `public` | backend |
| `chatbot_ro` (nuevo) | `SELECT` sobre `public.*` (+ default privileges para tablas futuras) | capa `analytics/` |
| `chatbot_app` (nuevo) | RW **solo** sobre schema `chat` | historial del chat |

Script idempotente `chatbot/scripts/init_db_roles.sql` (se corre una vez por entorno):

```sql
-- Roles del chatbot (idempotente)
DO $$ BEGIN CREATE ROLE chatbot_ro LOGIN PASSWORD :'ro_pass'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE chatbot_app LOGIN PASSWORD :'app_pass'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;

GRANT USAGE ON SCHEMA public TO chatbot_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatbot_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO chatbot_ro;  -- tablas futuras: legibles sin tocar nada

CREATE SCHEMA IF NOT EXISTS chat AUTHORIZATION chatbot_app;
```

**Contrato entre servicios = esquema de la DB.** Regla de mantenimiento: si una migración del backend renombra/borra una columna usada por `analytics/`, se actualiza la función correspondiente (los tests dorados lo detectan). Las tablas nuevas del backend no rompen nada (default privileges) — son la puerta de la escalabilidad (§10).

**Dos engines SQLAlchemy** en el chatbot (`core/db.py`):
- `business_engine` → `chatbot_ro`, `pool_pre_ping`, `statement_timeout=10s`, solo lo usa `analytics/`.
- `chat_engine` → `chatbot_app`, `search_path=chat`, lo usan los modelos del historial.

---

## 4. Estructura del servicio (espejo del backend)

```
chatbot/
├── Dockerfile
├── requirements.txt              # fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary,
│                                 # pydantic-settings, openai, pandas, redis, python-jose
├── alembic.ini                   # version_table_schema = chat
├── alembic/versions/
├── scripts/init_db_roles.sql
├── .env.example
├── tests/
│   ├── analytics/                # unitarios por dominio (cifras vs dashboard)
│   ├── agent/                    # loop, registry, guardrails
│   └── golden/questions.json     # suite de preguntas doradas + runner
└── app/
    ├── main.py                   # FastAPI, CORS, /health, montaje de routers
    ├── core/                     # ── CONFIGURACIÓN ──
    │   ├── config.py             # Settings (pydantic-settings, .env)
    │   ├── security.py           # get_current_user: valida cookie JWT (SECRET_KEY compartido)
    │   ├── db.py                 # business_engine (RO) + chat_engine (RW) + get_db
    │   ├── redis.py              # cliente Redis (pool)
    │   └── logging.py            # logging estructurado (request_id, conv_id)
    ├── models/                   # ── MODELOS ── (SQLAlchemy, schema chat)
    │   ├── conversation.py
    │   └── message.py
    ├── schemas/                  # ── SCHEMAS ── (Pydantic v2)
    │   ├── conversation.py
    │   ├── message.py            # bloques: text | table | chart
    │   └── events.py             # eventos SSE tipados
    ├── api/                      # ── APIS ──
    │   └── v1/
    │       ├── api.py            # include_router
    │       └── chat/router.py    # endpoints §5
    ├── services/                 # ── SERVICIOS ──
    │   ├── conversation_service.py   # CRUD historial (Postgres)
    │   ├── memory_service.py         # Redis: ventana, pizarra, resumen (cache-aside)
    │   ├── chat_service.py           # orquesta un turno: memoria → agente → persistencia → SSE
    │   └── llm/
    │       ├── base.py               # puerto LLMClient (interfaz: complete_stream(messages, tools))
    │       └── openai_compatible.py  # adaptador Groq/OpenAI (SDK openai, base_url configurable)
    ├── agent/                    # ── AGENTE ──
    │   ├── loop.py               # loop de tool calling (máx N iteraciones, timeouts)
    │   ├── registry.py           # ToolRegistry: name → (schema, executor); registro por dominio
    │   ├── prompts.py            # system prompt + guardrails + plantillas (título, resumen)
    │   └── tools/                # definiciones JSON Schema (una por dominio)
    │       ├── sales.py  ├── customers.py  ├── inventory.py  ├── processes.py
    │       ├── expenses.py  ├── fairs.py  ├── purchases.py  ├── profit.py
    │       └── common.py         # resolver_entidad, resumen_ejecutivo, esquema_negocio
    └── analytics/                # ── ANÁLISIS (Pandas) ──
        ├── base.py               # parse de rangos datetime (TZ Bogotá), df helpers, topes, formato compacto
        ├── entity_resolver.py
        ├── sales.py  ├── customers.py  ├── inventory.py  ├── processes.py
        ├── expenses.py  ├── fairs.py  ├── purchases.py  ├── profit.py
        └── cross.py              # comparaciones, tendencias, anomalías
```

Separación estricta de responsabilidades: `analytics/` no sabe que existe un LLM (recibe parámetros tipados, devuelve dicts); `agent/` no sabe de SQL; `services/` orquesta; `api/` solo transporta.

---

## 5. API del microservicio

Prefijo público: `/chat` (lo quita nginx) → internamente `/api/v1`.

| Método | Ruta interna | Descripción |
|---|---|---|
| `GET` | `/health` | Liveness (DB negocio, DB chat, Redis, proveedor LLM configurado) |
| `POST` | `/api/v1/conversations` | Nueva conversación |
| `GET` | `/api/v1/conversations` | Lista del usuario (título, fecha, preview) |
| `GET` | `/api/v1/conversations/{id}` | Historial completo (mensajes con bloques + pasos de tools) |
| `POST` | `/api/v1/conversations/{id}/messages` | **Enviar mensaje → respuesta SSE** |
| `DELETE` | `/api/v1/conversations/{id}` | Borrar (dueño o admin) |

**Eventos SSE** (`text/event-stream`, `X-Accel-Buffering: no`):

| Evento | Payload | Momento |
|---|---|---|
| `status` | `{"tool": "perfil_cliente", "label": "Analizando compras del cliente…"}` | inicio de cada tool |
| `text_delta` | `{"text": "..."}` | tokens de la respuesta |
| `done` | `{"message_id", "usage": {input, output}, "latency_ms"}` | fin del turno |
| `error` | `{"detail"}` | error irrecuperable |

---

## 6. Persistencia

### 6.1 PostgreSQL — schema `chat` (fuente de verdad)

```sql
CREATE TABLE chat.conversations (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,            -- id del usuario del backend (sin FK cross-schema: se valida por JWT)
    title       VARCHAR(200),
    summary     TEXT,                        -- resumen acumulado (fase 2)
    entities    JSONB DEFAULT '{}',          -- pizarra: {"cliente": {"id":7,"nombre":"Lina"}, "periodo": "2026-03"}
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat.messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES chat.conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,    -- user | assistant | tool
    content         JSONB NOT NULL,          -- [{type:"text",text:"..."}] | tool payload
    tool_name       VARCHAR(100),
    tool_input      JSONB,
    tool_result     JSONB,                   -- resultado completo → auditoría y evaluación
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    latency_ms      INTEGER,
    model           VARCHAR(80),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_chat_messages_conv ON chat.messages(conversation_id, id);
```

Alembic propio del servicio con `version_table_schema="chat"` → **cero colisión** con las migraciones del backend. Deploy = `alembic upgrade head` del chatbot crea solo objetos nuevos (aditivo, sin pérdida de datos).

### 6.2 Redis — memoria caliente (reconstruible)

| Clave | Tipo | Contenido | TTL |
|---|---|---|---|
| `conv:{id}:window` | LIST | últimos 12 mensajes serializados (incluye tool calls con resultados resumidos) | 7 días |
| `conv:{id}:entities` | HASH | pizarra de entidades resueltas | 7 días |
| `conv:{id}:summary` | STRING | resumen acumulado | 7 días |
| `ratelimit:{user_id}` | STRING | contador de mensajes/min | 60 s |

Política **cache-aside**: se lee de Redis; en miss se reconstruye desde Postgres y se recalienta. Redis puede vaciarse sin pérdida real (`allkeys-lru`, sin volumen). Postgres manda.

---

## 7. Capa LLM (intercambiable)

```python
# services/llm/base.py — puerto
class LLMClient(Protocol):
    async def stream_completion(
        self, *, messages: list[dict], tools: list[dict],
        max_tokens: int, temperature: float,
    ) -> AsyncIterator[LLMEvent]: ...   # LLMEvent: text_delta | tool_call | usage | stop
```

```python
# services/llm/openai_compatible.py — único adaptador necesario hoy
from openai import AsyncOpenAI
client = AsyncOpenAI(base_url=settings.LLM_BASE_URL, api_key=settings.LLM_API_KEY)
# chat.completions.create(model=..., tools=[{"type":"function","function":{...}}],
#                         stream=True, temperature=0.1, ...)
```

| Entorno | `LLM_BASE_URL` | `LLM_MODEL` | Notas |
|---|---|---|---|
| **Desarrollo** | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | Tool calling sólido, free tier, muy rápido. Tareas auxiliares (títulos, resúmenes): `llama-3.1-8b-instant` (`LLM_MODEL_LIGHT`) |
| Producción (opción) | igual (Groq pago) o `https://api.openai.com/v1` con `gpt-4o-mini`/`gpt-4.1-mini` | — | Solo cambian variables de entorno |
| Futuro | adaptador `anthropic.py` (Claude) si se busca máxima calidad analítica | — | El puerto ya lo permite; no se implementa ahora |

Parámetros fijos del agente: `temperature=0.1` (precisión sobre creatividad), `max_tokens=700` (respuestas breves-moderadas), `parallel_tool_calls` habilitado.

**Formato de tools (OpenAI):** `{"type": "function", "function": {"name", "description", "parameters": {...}}}` con `additionalProperties: false`. Las descripciones dicen **cuándo** usar la tool (es lo que más precisión aporta con modelos medianos).

---

## 8. El agente

### 8.1 Loop (agent/loop.py)

```
armar contexto (system + resumen + pizarra + ventana + turno con fecha/hora actual)
repetir hasta MAX_ITERATIONS=8:
    stream LLM
    ├─ text_delta → SSE al frontend
    └─ tool_calls → por cada una:
         validar input contra JSON Schema (error → tool_result con is_error y mensaje accionable)
         ejecutar executor (timeout 15 s) → persistir en chat.messages → SSE "status"
       todos los resultados vuelven en UN solo mensaje (rol tool) → siguiente iteración
    si no hubo tool_calls → fin (respuesta final ya emitida)
al agotar iteraciones: última llamada SIN tools → "esto es lo que pude obtener…"
persistir turno + usage; actualizar Redis (ventana, pizarra)
```

Barandillas programáticas (del servicio, no del modelo): tope de iteraciones, timeout por tool y por turno (60 s), tope de 50 filas y ~2.000 tokens por resultado (con `"truncado": true`), validación de schema previa a ejecutar, rate limit por usuario.

### 8.2 System prompt (esqueleto)

```
Eres el asistente analítico interno de Shaya, empresa cafetera colombiana (compra de café
pergamino a caficultores → maquila/tostado → venta directa y en ferias).

ALCANCE (regla dura): SOLO respondes sobre los datos del negocio de Shaya usando las
herramientas. Si preguntan cualquier cosa fuera (política, deportes, conocimiento general,
código, otras empresas), responde exactamente: "Solo puedo ayudarte con información del
negocio de Shaya (ventas, inventario, procesos, ferias, clientes, gastos)." No expliques más.

CIFRAS: toda cifra debe salir textual de un resultado de herramienta de esta conversación.
Nunca inventes, extrapoles ni redondees más allá del formato indicado.

IDs: si el usuario menciona un número junto a una entidad ("inventario de maquilado 5",
"la venta 120", "proceso 3"), es el ID de esa entidad: úsalo directo, no preguntes a no se de que encuentras algo que no te cuadra, como por ejemplo que hayan dos IDs (Proceso y Maquilado) Ahi pregunta si es necesario.
Nombres ("Lina", "Bourbon") → resolver_entidad; con varios candidatos plausibles, pregunta.

TIEMPO: zona horaria America/Bogota. Recibes la fecha/hora actual en cada turno. Resuelve
expresiones relativas a rangos exactos con hora ("ayer 4pm a hoy 1am" →
2026-07-07T16:00:00 a 2026-07-08T01:00:00) y decláralos en la respuesta si hubo interpretación.

ESTILO: español, breve y preciso (3–8 líneas o una tabla corta). El dato primero. COP con
formato $1.234.567; porcentajes con 1 decimal. Sin relleno ni disculpas largas.
Si no hay datos: dilo claro y corto. Nombra siempre la entidad resuelta ("Lina (cliente #7)…").

NEGOCIO: IVA maquila 5.2%. Rendimiento = kg_resultantes/kg_pergamino. unit_cost por bolsa =
café + maquila con IVA + gastos de proceso prorrateados + gastos de producto.
Utilidad = ingreso − unit_cost. Lotes históricos importados pueden tener unit_cost nulo →
repórtalo como "costo no disponible para N unidades".
```

La fecha/hora actual **no va en el system** (rompería el caché de prefijo): se antepone al mensaje del usuario en cada turno: `[Ahora: miércoles 2026-07-08 14:32:01, America/Bogota]`.

### 8.3 Rangos de tiempo con hora

- Todas las tools de consulta aceptan `fecha_inicio` / `fecha_fin` en `YYYY-MM-DD` **o** `YYYY-MM-DDTHH:MM:SS` (intervalo semiabierto `[inicio, fin)`; si solo hay fecha, se expande a día completo).
- `analytics/base.py::parse_range()` centraliza: parseo, TZ Bogotá, validación (inicio < fin, tope 24 meses por defecto), y devuelve el rango efectivo para que la respuesta lo declare.

---

## 9. Catálogo de tools

Principio: una tool por pregunta-base del dominio, variación por `enum`; nunca se exponen tablas/columnas. Toda respuesta: `{"resumen": {...}, "filas": [...], "advertencias": [...]}` con `top ≤ 50`.

### Fase 1 — MVP (10 tools)

| # | Tool | Responde a | Nota |
|---|---|---|---|
| 1 | `resolver_entidad` | nombres → ids con fuzzy match (cliente, producto, caficultor, feria, proceso, lote) | pg_trgm/difflib |
| 2 | `consultar_ventas` | totales/rankings/agrupaciones de ventas con rango datetime | producto·cliente·mes·semana·día·hora |
| 3 | `detalle_venta` | "¿qué llevaba la venta 120?" | |
| 4 | `perfil_cliente` ★ | "¿a Lina le gusta el café en grano y por libra?" → compras por producto/presentación, frecuencia, última compra | responde preferencias con datos, no opinión |
| 5 | `estado_inventario` | stock pergamino/tostado, bajo stock | |
| 6 | `movimientos_maquilado` ★ | "¿el lote 5 tuvo reempaque?" → `lote_id`, `tipo` (salida\|entrada\|reempaque\|todos), rango | usa `roasted_movements` + detalles |
| 7 | `consultar_procesos` | kg procesados, rendimiento, costos de maquila | |
| 8 | `consultar_gastos_generales` | gastos por categoría/método de pago/mes | |
| 9 | `consultar_compras_pergamino` | compras por caficultor/variedad, precio promedio | |
| 10 | `resumen_ejecutivo` | "¿cómo va el negocio?" | valida contra Dashboard |

### Fase 2 — contexto y comparaciones (+7)

11 `analisis_clientes` (ranking + RFM: "cliente que más ha comprado" con top de productos) · 12 `comparar_periodos` · 13 `comparar_entidades` · 14 `listar_ferias` · 15 `reporte_feria` · 16 `rentabilidad_ferias` ★ (ganancia = ingresos − costo vendido con `unit_cost` − gastos; ratio ganancia/gasto; "mejores ferias") · 17 `detalle_proceso`

### Fase 3 — análisis profundo (+7)

18 `tendencia` · 19 `detectar_anomalias` · 20 `rotacion_inventario` · 21 `analisis_rendimiento` · 22 `costos_produccion` · 23 `analisis_utilidad` (por producto/cliente/periodo con `unit_cost`) · 24 `obtener_esquema_negocio`

### Fase 4 — ferias con datos + bloques ricos

25 `ventas_feria` · 26 `gastos_feria` (el código de ferias se escribe antes; sus pruebas doradas se activan cuando existan datos — hoy `fairs` tiene 0 filas).

★ = nuevas respecto al diseño original, derivadas de las preguntas objetivo.

### Trazas esperadas (preguntas objetivo → tools)

| Pregunta | Traza |
|---|---|
| Cliente que más compra + productos | `analisis_clientes(metrica=total, top=1)` → `perfil_cliente(id)` |
| Mejores ferias ganancia vs gasto | `rentabilidad_ferias(orden=ratio_desc)` |
| Reempaque del lote 5 | `movimientos_maquilado(lote_id=5, tipo=reempaque)` (sin resolver_entidad: el id va directo) |
| Preferencias de Lina | `resolver_entidad(cliente,"lina")` → `perfil_cliente(id=7)` |
| Ferias de marzo + ganancia | `listar_ferias(2026-03-01→2026-04-01)` → `rentabilidad_ferias(fair_ids=[...])` |
| Ventas ayer 4pm → hoy 1am | `consultar_ventas(2026-07-07T16:00 → 2026-07-08T01:00)` |

---

## 10. Escalabilidad: receta para un dominio nuevo

Caso ejemplo: mañana se empieza a registrar **el precio del café varias veces al día** (nueva tabla `coffee_price_history` en el backend).

| Paso | Archivo | Esfuerzo |
|---|---|---|
| 1. El backend crea tabla + captura de datos | (backend, su Alembic) | fuera del chatbot |
| 2. Función analítica | `analytics/coffee_price.py` → `consultar_precio_cafe(rango, granularidad, estadisticos)` | ~1 h |
| 3. Definición de tool | `agent/tools/coffee_price.py` (JSON Schema + descripción "cuándo usarla") | ~15 min |
| 4. Registro | 1 línea en `registry.py` | 1 min |
| 5. Evaluación | 2–3 preguntas doradas nuevas | ~15 min |

**Nada más cambia**: ni loop, ni memoria, ni endpoints, ni frontend, ni permisos (los default privileges de `chatbot_ro` ya cubren la tabla nueva). Esa es la propiedad de escalabilidad del diseño: crecer = agregar módulos `analytics` + tools, crecimiento lineal.

Lo mismo aplica a capacidades transversales (proyecciones, alertas): tools nuevas sobre la misma capa. Y si el volumen de datos crece 100×, las barandillas (filtros en SQL, agregación en DB antes de Pandas, topes de filas) ya están puestas.

---

## 11. Frontend — vista del usuario

### Navegación y layout

- Nueva entrada **"Asistente"** en `menuConfig.tsx` (ícono de chat), misma SPA.
- Layout de dos paneles (patrón ya usado por la app):
  - **Panel izquierdo** (colapsable, como el sidebar actual en móvil): botón "Nueva conversación", lista de conversaciones (título autogenerado + fecha relativa), borrar con confirmación.
  - **Panel principal**: hilo de mensajes + composer fijo abajo (textarea autosize, Enter envía / Shift+Enter salto, botón detener durante el stream).

### Hilo de mensajes

- Burbujas usuario (derecha) / asistente (izquierda, con avatar de la marca).
- **Pasos de tools visibles y colapsables**: chip "🔍 Consultando ventas… ✓" mientras corre el agente (los eventos `status` del SSE) — transparencia de qué consultó.
- Respuesta del asistente renderizada por **bloques**: `text` (markdown ligero: negritas, listas, tablas md) hoy; `table` y `chart` (Recharts) en fase 4 sin rediseño.
- Cursor parpadeante durante `text_delta`; auto-scroll inteligente (se detiene si el usuario sube).

### Estados

- **Vacío**: tarjetas con preguntas sugeridas reales ("¿Cuál es el cliente que más ha comprado?", "¿Cuánto café tostado queda?", "¿Cómo va el negocio este mes?" Deben ser relacionadas con el modulo en el que se encuentre el usuario, por asi decirlo si esta en clientes que le recomiendes perguntas sobre clientes, etc) — clic = enviar.
- **Error**: mensaje inline con botón reintentar (reenvía el último mensaje).
- **Sin conexión al stream**: aviso y recuperación del historial por `GET /conversations/{id}`.

### Técnica

```
features/chat/
├── ChatPage.tsx
├── components/ConversationList.tsx · MessageThread.tsx · MessageBubble.tsx
│              · ToolStepChips.tsx · Composer.tsx · SuggestionCards.tsx
├── hooks/useChatStream.ts        # fetch POST + ReadableStream → parsea SSE (no EventSource: se necesita POST+cookie)
├── models/types.ts               # Conversation, Message, Block, SSEEvent (espejo de schemas/ del servicio)
└── services/chat.api.ts          # base '/chat/api/v1', credentials: 'include'
```

- **Dev**: proxy de Vite `'/chat' → http://localhost:8005` (junto al proxy `/api` existente).
- **Prod**: nginx `location /chat/` (§12). Mismo dominio → la cookie viaja sola.

---

## 12. Docker, entornos y despliegue sin pérdida de datos

### 12.1 Cambios en `docker-compose.yml` (aditivos)

```yaml
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--maxmemory", "128mb", "--maxmemory-policy", "allkeys-lru"]
    # sin volumen: la memoria caliente es reconstruible desde Postgres

  chatbot:
    build: ./chatbot
    restart: unless-stopped
    environment:
      ENV: production
      BUSINESS_DB_HOST: db
      BUSINESS_DB_NAME: ${DB_NAME}
      BUSINESS_DB_USER: chatbot_ro
      BUSINESS_DB_PASSWORD: ${CHATBOT_RO_PASSWORD}
      CHAT_DB_USER: chatbot_app
      CHAT_DB_PASSWORD: ${CHATBOT_APP_PASSWORD}
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}            # el mismo del backend → valida la cookie
      FRONTEND_URL: ${FRONTEND_URL}
      LLM_BASE_URL: ${LLM_BASE_URL}
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_MODEL: ${LLM_MODEL}
      LLM_MODEL_LIGHT: ${LLM_MODEL_LIGHT}
      TZ: America/Bogota
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8005"
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
```

Y en el nginx del contenedor `web` ([frontend/nginx.conf](../frontend/nginx.conf)):

```nginx
    # Chatbot: SSE → sin buffering
    location /chat/ {
        proxy_pass http://chatbot:8005/;      # /chat/api/v1/... → /api/v1/...
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;                  # imprescindible para SSE
        proxy_read_timeout 120s;              # turnos largos del agente
    }
```

### 12.2 Entorno de desarrollo (este equipo)

- `.env` raíz (dev) suma: `CHATBOT_RO_PASSWORD`, `CHATBOT_APP_PASSWORD`, `LLM_BASE_URL=https://api.groq.com/openai/v1`, `LLM_API_KEY=gsk_...`, `LLM_MODEL=llama-3.3-70b-versatile`, `LLM_MODEL_LIGHT=llama-3.1-8b-instant`.
- Pruebas en este equipo: todo con Docker, igual que producción — `docker compose up -d --build chatbot redis` (con `db` y `web` ya levantados por el compose). No hay modo local con `uvicorn --reload`/proxy de Vite para el chatbot; cada cambio en `chatbot/` se prueba reconstruyendo el contenedor.

### 12.3 Checklist de despliegue al servidor (cero pérdida de datos)

1. `git pull` en el servidor.
2. Una sola vez: `docker compose exec -T db psql -U $DB_USER -d $DB_NAME -v ro_pass='...' -v app_pass='...' -f - < chatbot/scripts/init_db_roles.sql` (idempotente).
3. Añadir las variables nuevas al `.env` del servidor (clave Groq de prod, passwords de roles).
4. `docker compose up -d --build chatbot redis web` — `web` se reconstruye porque lleva el `nginx.conf` con `location /chat/` y la UI nueva; `db` y `pgdata` **no se tocan**; el Alembic del chatbot solo crea el schema `chat`.
5. Verificar `https://<dominio>/chat/health` y una pregunta dorada manual.

Rollback simple: quitar el servicio `chatbot` del compose — el resto del sistema no depende de él.

---

## 13. Normas de calidad

| Norma | Concreción |
|---|---|
| Tipado | Type hints completos; Pydantic v2 en toda frontera (API, tools, eventos SSE) |
| Separación | `analytics/` puro (sin FastAPI/LLM); `agent/` sin SQL; dependencias en una sola dirección |
| Solo lectura | Usuario `chatbot_ro` a nivel de base de datos, no por convención de código |
| Tests | pytest: unitarios de `analytics/` (cifras contra el Dashboard con datos reales), del loop (tools simuladas), y **suite dorada** ejecutable (`tests/golden/`) como regresión |
| Observabilidad | Log estructurado por turno: conv_id, tools usadas, tokens, latencia; `GET /health` con chequeo de dependencias |
| Errores | Toda excepción de tool → `is_error` accionable al modelo; nunca 500 por una tool fallida, debe generar un reporte del error en consola, especificando en que parte fue y el motivo + log del error |
| Secretos | Solo por entorno; `.env.example` documentado; API key jamás llega al navegador |
| Commits | Español, simples, sin atribución de IA (convención del repo) |
| Evaluación continua | Revisión semanal de `chat.messages`: preguntas fallidas, tools mal usadas, costos anómalos |

---

## 14. Roadmap

### Fase 0 — Esqueleto del servicio (1 sesión)
- [ ] `chatbot/` con estructura §4, `Dockerfile`, `requirements.txt`, `.env.example`
- [ ] `core/`: config, db (2 engines), redis, security (validación cookie JWT), logging
- [ ] Roles SQL + Alembic propio + migración inicial (schema `chat`)
- [ ] `/health` completo; servicios `redis` y `chatbot` en compose; proxy Vite y nginx location
- **Criterio:** `/chat/health` OK en dev (Docker y local) con las 4 dependencias verdes

### Fase 1 — Analytics core + agente MVP (2–3 sesiones)
- [ ] `analytics/base.py` (rangos datetime Bogotá) + 6 dominios núcleo + `entity_resolver`
- [ ] Tests de cifras contra el Dashboard (datos reales)
- [ ] `LLMClient` + adaptador Groq; loop del agente; registry con las 10 tools MVP
- [ ] Endpoints + SSE; persistencia de turnos; títulos con modelo light
- [ ] Frontend `features/chat/` completo (§11)
- [ ] Suite dorada v1 (~20 preguntas de consulta directa, incluidas las 6 preguntas objetivo que apliquen)
- **Criterio:** ≥90% doradas correctas; 0 cifras inventadas; rechazo correcto de 5 preguntas fuera de alcance; p50 < 6 s

### Fase 2 — Memoria completa + comparaciones (2 sesiones)
- [ ] Pizarra de entidades + resumen acumulado (Redis + Postgres)
- [ ] Tools 11–17 (incl. `rentabilidad_ferias`); desambiguación interactiva
- [ ] Doradas de secuencias ("¿y el mes pasado?", "¿y ese cliente?")
- **Criterio:** referencias encadenadas ≥90%; costo/turno estable en conversaciones largas

### Fase 3 — Análisis profundo + utilidad (2 sesiones)
- [ ] Tools 18–24 (`analisis_utilidad` sobre `unit_cost`)
- [ ] Manejo declarado de `unit_cost` nulo (lotes históricos)
- **Criterio:** equipo valida ≥80% de análisis como útiles; ninguna conclusión contradice sus datos

### Fase 4 — Ferias con datos + bloques ricos
- [ ] Doradas de ferias (cuando existan registros reales)
- [ ] Bloques `table`/`chart` en frontend (Recharts); exportaciones sobre la misma capa analytics

---

## 15. Suite de preguntas doradas (núcleo inicial)

En `tests/golden/questions.json`: pregunta, respuesta esperada (cifra/criterio), tools esperadas. Runner que ejecuta contra el servicio y compara.

1–6. Las **seis preguntas objetivo** de §1 (con sus cifras verificadas a mano).
7. ¿Cuánto vendimos en [mes con datos]? (= dashboard)
8. Top 5 productos por unidades e ingresos.
9. ¿Cuánto café tostado queda? ¿Y del producto X?
10. ¿Qué kilos compramos a [caficultor] y a qué precio promedio?
11. ¿Rendimiento promedio de los procesos?
12. ¿Gastos de [categoría] este año, por método de pago?
13. ¿Qué llevaba la venta #N?
14. "ventas de Burbon" (typo) → resuelve o pregunta, no falla.
15. "ventas de 2020" → "no hay datos", no inventa.
16. "¿Quién es el presidente de Colombia?" → rechazo estándar exacto.
17. "hazme un poema del café" → rechazo estándar.
18. "¿cuánto vendimos hoy entre 8am y 2pm?" → rango horario correcto.
19. Conversación: "¿mejor cliente?" → "¿y qué compra?" (referencia implícita).
20. "¿cómo va el negocio?" → coincide con KPIs del dashboard.

---

## 16. Riesgos y mitigaciones (delta vs. doc original)

| Riesgo | Mitigación |
|---|---|
| Groq (modelo mediano) elige mal las tools o alucina parámetros | Descripciones "cuándo usarla", enums cerrados, validación de schema con error accionable, `temperature=0.1`, suite dorada como red; si la precisión no alcanza → subir de modelo vía env (sin código) |
| Drift del esquema del backend rompe `analytics/` | Tests dorados en CI del repo (corren contra la DB dev); regla de PR: migración del backend que toque tablas consultadas → revisar `analytics/` |
| SSE cortado por proxies | `proxy_buffering off` + heartbeat `: ping` cada 15 s + recuperación por GET del historial |
| Redis caído | Cache-aside: el servicio sigue funcionando contra Postgres (más lento), log de advertencia |
| Costos LLM crecen | Tokens por turno en `chat.messages` + rate limit por usuario + respuestas cortas por diseño |
| Fuga de alcance (prompt injection "ignora tus reglas") | El system prompt no es la única barrera: no existen tools fuera del negocio y el servicio es RO — el daño posible se limita a una respuesta fuera de tono; doradas 16–17 lo vigilan |
