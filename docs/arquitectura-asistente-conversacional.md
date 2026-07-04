# Arquitectura del Asistente Conversacional de Shaya

> Documento de diseño. No contiene código ni implementación; define la arquitectura, las decisiones y el plan de construcción de un chatbot analítico sobre los datos del sistema Shaya (FastAPI + SQLAlchemy + PostgreSQL / React + Vite + TS).

---

## 0. Resumen ejecutivo de las decisiones

| Decisión | Elección | Alternativa descartada |
|---|---|---|
| Ubicación del agente | Backend (nuevo módulo `chat/` siguiendo el patrón router/service/schema existente) | Agente en el frontend hablando directo con el LLM |
| Granularidad de tools | **Híbrida**: ~18 herramientas parametrizables de granularidad media, agrupadas por dominio | 1 mega-tool genérica / 60+ micro-tools |
| Acceso a datos | Capa nueva `analytics/` que consulta vía SQLAlchemy, agrega con **Pandas** y devuelve JSON compacto | LLM generando SQL; reutilizar los services CRUD tal cual |
| Memoria conversacional | Historial persistido en DB + ventana deslizante + **pizarra de entidades resueltas** (slots) | Reenviar toda la conversación siempre |
| Resolución de nombres | Tool explícita `resolver_entidad` con búsqueda difusa | Confiar en que el LLM adivine IDs |
| Loop del agente | Tool-calling iterativo (máx. N iteraciones) orquestado por el backend, respuesta por streaming (SSE) | Pipeline de un solo paso pregunta→tool→respuesta |

Una observación crítica al planteamiento inicial se detalla en §11 (la más importante: **el sistema hoy no almacena costo unitario por producto terminado**, lo que limita cualquier pregunta de "utilidad" — hay que definir el costo derivado del proceso de maquila antes de prometer análisis de rentabilidad).

---

## 1. Arquitectura general

### 1.1 Componentes

```
┌─────────────┐   POST /api/v1/chat/message (SSE)   ┌──────────────────────────────┐
│  Frontend   │ ───────────────────────────────────▶│  Backend FastAPI              │
│  React      │ ◀─────────────── stream ────────────│                              │
│  ChatPage   │                                     │  ┌────────────────────────┐  │
└─────────────┘                                     │  │ ChatService (agente)   │  │
                                                    │  │  - loop de tool calling│  │
                                                    │  │  - memoria / slots     │  │
                                                    │  └───────┬────────────────┘  │
                                                    │          │ tools (JSON)      │
                                       ┌────────────┼──────────▼───────────────┐   │
                                       │  LLM (API) │  ToolRegistry            │   │
                                       │  Claude    │  (catálogo + validación) │   │
                                       └────────────┼──────────┬───────────────┘   │
                                                    │          ▼                   │
                                                    │  ┌────────────────────────┐  │
                                                    │  │ AnalyticsService(s)    │  │
                                                    │  │ SQLAlchemy → DataFrame │  │
                                                    │  │ Pandas: agregaciones   │  │
                                                    │  └───────┬────────────────┘  │
                                                    └──────────┼───────────────────┘
                                                               ▼
                                                        PostgreSQL
```

- **Frontend**: nueva feature `src/features/chat/` con el mismo patrón del proyecto (`Page.tsx`, `services/chat.api.ts`, `models/types.ts`). Una entrada más en el switch de `HomePage.tsx`. Renderiza el stream de la respuesta y, en fases futuras, "bloques ricos" (tablas pequeñas, gráficos).
- **Backend — módulo `chat/`**: nuevo paquete `backend/app/api/api_v1/chat/` con `router.py`, `service.py`, `schema.py`, igual que sales o fairs. El router expone crear conversación, enviar mensaje, listar historial. Reutiliza `get_current_user` — el chat hereda la autenticación existente.
- **ChatService (orquestador del agente)**: recibe el mensaje, arma el contexto (system prompt + memoria + mensaje), llama al LLM, ejecuta las tools que el modelo pida, devuelve los resultados al modelo y repite hasta que el modelo emite texto final. Es el **único** componente que habla con el LLM.
- **ToolRegistry**: catálogo declarativo de herramientas (nombre, descripción, JSON Schema de parámetros, función ejecutora). Valida parámetros antes de ejecutar y normaliza errores a mensajes que el modelo puede corregir ("la feria 'Inovo' no existe; opciones cercanas: Innovo, Ciclovía").
- **AnalyticsServices**: capa nueva paralela a los services CRUD existentes (`backend/app/analytics/` o `chat/tools/`). Cada función: consulta acotada con SQLAlchemy (filtros en SQL, no en Python), pasa a DataFrame de Pandas, agrega/pivota/calcula, y devuelve un dict pequeño y ya resumido. **El LLM nunca ve filas crudas, solo agregados.**
- **Base de datos**: además de las tablas de negocio, dos tablas nuevas: `chat_conversations` y `chat_messages` (rol, contenido, tool calls serializados, tokens usados).

### 1.2 Flujo de un mensaje (extremo a extremo)

1. El usuario escribe "¿Cuál fue el producto más vendido en la feria Innovo?" en `ChatPage`.
2. Frontend hace `POST /chat/conversations/{id}/message` con el texto; abre el stream SSE.
3. `ChatService` carga la memoria de la conversación (§5): últimos K turnos + resumen + pizarra de entidades.
4. Llama al LLM con: system prompt (rol, fecha actual, catálogo de negocio mínimo, reglas), memoria, mensaje.
5. El LLM decide llamar `resolver_entidad(tipo="feria", texto="Innovo")` → el backend responde `{id: 4, nombre: "Innovo", estado: "closed", fechas: ...}`.
6. El LLM llama `ventas_feria(fair_id=4, agrupar_por="producto", metrica="cantidad", top=5)` → el AnalyticsService une `fair_sales` + `fair_inventories` + `detail_roasted_coffees` + `products`, agrega con Pandas y devuelve ~5 filas JSON con totales.
7. El LLM redacta la respuesta en lenguaje natural; el backend la transmite por el stream y persiste todo el turno (mensaje, tool calls, resultado, respuesta) en `chat_messages`, y actualiza la pizarra de entidades (`última_feria = Innovo(4)`).
8. Frontend muestra la respuesta; los tool calls pueden mostrarse como "pasos" colapsables (transparencia y debugging).

### 1.3 Por qué el agente vive en el backend

- La API key del LLM nunca llega al navegador.
- Las tools son funciones Python con acceso a la sesión de SQLAlchemy y a Pandas — tienen que ejecutarse en el servidor.
- Permite imponer permisos: el chat ve lo que el rol del usuario puede ver (p. ej., costos solo admin, si se decide).
- El historial queda persistido y auditable en PostgreSQL.

---

## 2. Catálogo de herramientas

Antes del catálogo, dos herramientas transversales que sostienen todo lo demás:

### 2.0 Transversales

**`resolver_entidad`**
- **Objetivo**: convertir nombres en lenguaje natural a IDs canónicos, con búsqueda difusa (ILIKE + similitud) y desambiguación.
- **Parámetros**: `tipo` (feria | producto | cliente | caficultor | proceso | usuario), `texto`, `limite` (default 5).
- **Respuesta**: lista de candidatos `{id, nombre, metadatos breves}` o coincidencia exacta única.
- **Cuándo**: siempre que el usuario mencione una entidad por nombre y no esté ya en la pizarra de la conversación.
- **Ejemplos**: "la feria Innovo", "el cliente Juan", "el café Bourbon 250g".

**`obtener_esquema_negocio`**
- **Objetivo**: devolver al modelo, bajo demanda, el mini-diccionario del dominio: qué métricas existen por dominio, qué agrupaciones admite cada tool, rangos de fechas con datos, y definiciones (p. ej. "utilidad = ingreso − costo derivado de maquila − gastos"). Evita inflar el system prompt con todo esto de forma permanente.
- **Parámetros**: `dominio` (opcional).
- **Cuándo**: preguntas ambiguas o cuando el modelo duda de qué métrica usar.

### 2.1 Ventas (módulo `sales`)

**`consultar_ventas`**
- **Objetivo**: agregación flexible sobre `sales` + `detail_sales` (+ `detail_roasted_coffees` + `products` + `customers`).
- **Parámetros**: `fecha_inicio`, `fecha_fin`, `agrupar_por` (producto | cliente | mes | semana | día | usuario | ninguno), `metrica` (total | subtotal | cantidad | num_ventas | ticket_promedio), `filtro_producto_id`, `filtro_cliente_id`, `estado` (completed | in_progress), `orden` (asc | desc), `top` (default 10, máx 50).
- **Respuesta**: `{resumen: {total, num_registros, periodo}, filas: [...máx top...]}`.
- **Cuándo**: cualquier pregunta sobre ventas directas (no de feria).
- **Ejemplos**: "¿cuánto vendimos en marzo?", "top 5 productos por ventas este año", "¿a qué cliente le hemos vendido más?".

**`detalle_venta`**
- **Objetivo**: traer una venta puntual con sus líneas (equivale al GET by id existente, pero resumido).
- **Parámetros**: `sale_id`.
- **Ejemplos**: "¿qué llevaba la venta 120?".

### 2.2 Ferias (módulo `fairs`)

**`listar_ferias`**
- **Parámetros**: `fecha_inicio`, `fecha_fin`, `estado` (open | closed), `top`.
- **Respuesta**: por feria: nombre, fechas, ubicación, total vendido, total gastos, unidades vendidas.
- **Ejemplos**: "¿qué ferias hicimos este año?", "¿cuál fue la mejor feria?" (el modelo pide orden por total).

**`reporte_feria`**
- **Objetivo**: reporte consolidado de UNA feria — reutiliza la lógica de `get_fair_report` que ya existe en `FairService`: ventas por producto, inventario inicial/restante, gastos, neto.
- **Parámetros**: `fair_id`, `nivel_detalle` (resumen | por_producto | completo).
- **Ejemplos**: "¿cómo le fue a Innovo?", "¿qué producto se vendió más en Ciclovía?".

**`ventas_feria`**
- **Objetivo**: agregación flexible sobre `fair_sales` de una o varias ferias.
- **Parámetros**: `fair_ids` (lista), `fecha_inicio/fin` (para filtrar dentro de la feria, p. ej. "el sábado"), `agrupar_por` (producto | feria | día | hora), `metrica` (total | cantidad | ticket_promedio), `top`.
- **Ejemplos**: "¿a qué hora se vende más en las ferias?", "ventas por día en Ciclovía".

**`gastos_feria`**
- **Parámetros**: `fair_ids`, `agrupar_por` (feria | concepto), `top`.
- **Ejemplos**: "¿cuánto gastamos en Innovo?", "¿qué feria fue más cara de montar?".

### 2.3 Inventario (pergamino + producto terminado)

**`estado_inventario`**
- **Objetivo**: fotografía actual del stock. Cubre pergamino (`parchments.remaining_quantity`) y tostado (`detail_roasted_coffees.remaining_quantity`).
- **Parámetros**: `tipo` (pergamino | tostado | ambos), `filtro_producto_id`, `solo_bajo_stock` (bool, con umbral), `top`.
- **Ejemplos**: "¿cuánto café Bourbon queda?", "¿qué productos están por agotarse?".

**`movimientos_inventario`**
- **Objetivo**: historial agregado de `inventory_movements` + `roasted_movements` (entradas/salidas de maquilado).
- **Parámetros**: `fecha_inicio/fin`, `tipo` (entrada | salida | ambos), `origen` (venta | feria | movimiento_manual | proceso), `agrupar_por` (producto | mes | origen), `top`.
- **Ejemplos**: "¿qué salidas de café hubo en abril?", "¿cuánto café salió hacia ferias este año?".

**`rotacion_inventario`**
- **Objetivo**: velocidad de consumo por producto (unidades vendidas/mes vs. stock actual → meses de cobertura). Cálculo puro de Pandas.
- **Parámetros**: `ventana_meses` (default 3), `top`.
- **Ejemplos**: "¿qué producto rota más rápido?", "¿para cuánto alcanza el stock actual?".

### 2.4 Procesos / maquila (módulos `processes`, `roasted_coffee`)

**`consultar_procesos`**
- **Objetivo**: agregación sobre `processes` + `detail_processes`: kilos procesados, rendimiento, costos de maquila.
- **Parámetros**: `fecha_inicio/fin`, `agrupar_por` (mes | caficultor | variedad | ninguno), `metrica` (kg_procesados | kg_resultantes | rendimiento_promedio | costo_total), `top`.
- **Ejemplos**: "¿cuántos kilos tostamos este trimestre?", "¿qué rendimiento promedio tuvimos?", "¿el rendimiento está mejorando?".

**`detalle_proceso`**
- **Parámetros**: `process_id` o `invoice_number`.
- **Ejemplos**: "¿qué salió del proceso con factura 0453?".

**`analisis_rendimiento`**
- **Objetivo**: distribución del yield (%): promedio, desviación, mejores/peores lotes, correlación con variedad/altitud/humedad del pergamino de origen.
- **Parámetros**: `fecha_inicio/fin`, `dimension` (variedad | altitud | humedad | caficultor).
- **Ejemplos**: "¿qué variedad rinde mejor al tostar?", "¿la humedad afecta el rendimiento?".

### 2.5 Compras / caficultores

**`consultar_compras_pergamino`**
- **Objetivo**: agregación sobre `parchments`: kilos comprados, precio promedio, por caficultor/variedad/mes.
- **Parámetros**: `fecha_inicio/fin`, `agrupar_por` (caficultor | variedad | mes | altitud), `metrica` (kg | costo_total | precio_promedio_kg), `top`.
- **Ejemplos**: "¿a quién le compramos más café?", "¿cómo ha variado el precio del pergamino?".

### 2.6 Clientes

**`analisis_clientes`**
- **Objetivo**: métricas por cliente combinando `sales`: frecuencia, recencia, monto (RFM simplificado), última compra.
- **Parámetros**: `metrica` (total_comprado | frecuencia | recencia | ticket_promedio), `segmento` (activos | inactivos | nuevos | todos), `umbral_inactividad_dias` (default 90), `top`.
- **Ejemplos**: "¿qué clientes dejaron de comprar?", "¿quiénes son nuestros mejores clientes?", "¿cuántos clientes nuevos hubo este año?".

### 2.7 Comparaciones y análisis (transversales)

Estas son las que convierten al chatbot en analista y no en consultor de tablas:

**`comparar_periodos`**
- **Objetivo**: misma métrica en dos ventanas de tiempo, con delta absoluto y porcentual. Wrapper de Pandas sobre las tools de dominio.
- **Parámetros**: `dominio` (ventas | ferias | procesos | compras), `metrica`, `periodo_a`, `periodo_b`, `agrupar_por` (opcional).
- **Ejemplos**: "compara este trimestre con el anterior", "¿vendimos más que el año pasado en el mismo mes?".

**`comparar_entidades`**
- **Objetivo**: comparar N entidades del mismo tipo (ferias, productos, clientes) sobre un set de métricas, devolviendo tabla compacta + deltas.
- **Parámetros**: `tipo`, `ids` (2–5), `metricas` (lista), `periodo` (opcional).
- **Ejemplos**: "compara Innovo contra Ciclovía", "¿Bourbon o Geisha, cuál vende más?".

**`tendencia`**
- **Objetivo**: serie temporal de una métrica con granularidad elegida + pendiente/dirección calculada en Pandas (regresión simple o variación media), para que el modelo no tenga que inferir tendencias de números sueltos.
- **Parámetros**: `dominio`, `metrica`, `granularidad` (día | semana | mes), `fecha_inicio/fin`, `filtros`, `incluir_estadisticos` (bool).
- **Respuesta**: serie (máx ~36 puntos), pendiente, % de cambio, meses pico/valle.
- **Ejemplos**: "¿qué productos muestran tendencia creciente?", "¿las ventas van subiendo?".

**`detectar_anomalias`**
- **Objetivo**: valores fuera de rango (z-score / IQR sobre la serie) — meses atípicos, ventas inusuales, rendimientos anómalos.
- **Parámetros**: `dominio`, `metrica`, `granularidad`, `periodo`, `sensibilidad`.
- **Ejemplos**: "¿hubo algo raro en las ventas de mayo?", "¿algún proceso tuvo rendimiento anormal?".

**`resumen_ejecutivo`**
- **Objetivo**: paquete precalculado del periodo (reusa `DashboardService` + agregados clave de cada dominio): ventas totales, mejor feria, mejor producto, stock crítico, kilos procesados, clientes inactivos. Una sola llamada para preguntas abiertas.
- **Parámetros**: `periodo` (mes | trimestre | año | rango).
- **Ejemplos**: "¿cómo va el negocio?", "dame un resumen del último trimestre", "¿qué conclusiones sacas del Q1?".

### 2.8 Recuento

~18 tools: 2 transversales + 2 ventas + 4 ferias + 3 inventario + 3 procesos + 1 compras + 1 clientes + 5 análisis. Es un número cómodo: cabe en el prompt sin saturar (~3–4k tokens de definiciones) y cubre todos los módulos reales del sistema.

---

## 3. ¿Herramientas específicas o genéricas? — Decisión: híbrido de granularidad media

Los dos extremos fallan:

**Muchas micro-tools** (`producto_mas_vendido_en_feria`, `ventas_de_marzo`, …):
- ❌ Mantenibilidad: cada pregunta nueva = tool nueva; el catálogo crece sin límite.
- ❌ Tokens: 60 definiciones de tools se pagan en **cada** llamada al LLM.
- ❌ Escalabilidad: combinaciones (producto × feria × periodo × métrica) explotan combinatoriamente.
- ✅ Único pro: el modelo casi no puede equivocarse de parámetros.

**Una mega-tool genérica** (`consultar(entidad, filtros, agrupaciones, métricas, joins...)`):
- ❌ Es SQL disfrazado: el modelo debe conocer el esquema y las relaciones → más errores, más alucinación de campos, y viola el espíritu de la restricción "no SQL".
- ❌ Backend complejísimo: hay que implementar un query-builder genérico y seguro.
- ❌ Validación débil: el espacio de entradas inválidas es enorme.
- ✅ Único pro: catálogo mínimo.

**El punto medio elegido — una tool parametrizable por dominio + tools analíticas transversales:**
- **Mantenibilidad**: cada tool mapea a un AnalyticsService de ~1 responsabilidad; agregar una métrica es agregar un valor a un enum y una rama de Pandas, no una tool nueva.
- **Facilidad para el modelo**: los enums (`agrupar_por`, `metrica`) actúan como barandillas — el modelo elige de una lista cerrada en lugar de inventar. Los LLM actuales son muy fiables con este patrón.
- **Tokens**: ~18 definiciones ≈ 3–4k tokens fijos, aceptable; y cada respuesta de tool es un agregado pequeño.
- **Backend**: cada dominio tiene UNA consulta base con joins conocidos y fijos; Pandas hace el pivoteo según parámetros. Nada de query-builder genérico.
- **Escalabilidad**: un dominio nuevo = una tool nueva; una capacidad nueva (p. ej. proyecciones) = una tool transversal nueva. Crecimiento lineal, no combinatorio.

Regla práctica de diseño: **una tool por "pregunta base" del dominio, con la variación expresada en parámetros enumerados; nunca parámetros que expongan el esquema físico (nombres de tablas/columnas).**

---

## 4. Capacidades del asistente

Agrupadas de menor a mayor sofisticación (las fases del roadmap §10 siguen este orden):

**Consulta directa**
1. Consultas puntuales por entidad ("¿cuánto queda de X?", "¿qué llevaba la venta 120?").
2. Agregaciones con filtros ("ventas de marzo por producto").
3. Rankings / top-N ("mejores clientes", "producto más vendido en Innovo").
4. Fotografía de inventario y alertas de stock bajo.

**Comparación**
5. Entidad vs. entidad (Innovo vs. Ciclovía; Bourbon vs. Geisha).
6. Periodo vs. periodo (Q1 vs. Q2; marzo 2025 vs. marzo 2026).
7. Canal vs. canal (ventas directas vs. ventas en feria).

**Análisis**
8. Tendencias (productos crecientes/decrecientes, estacionalidad de ferias).
9. Detección de anomalías (mes atípico, proceso con rendimiento anómalo).
10. Correlaciones de producción (variedad/altitud/humedad vs. rendimiento de tostado).
11. Análisis de clientes: churn ("dejaron de comprar"), RFM, clientes nuevos.
12. Rotación y cobertura de inventario.
13. Análisis financiero de feria: ingresos − gastos = neto; margen por feria. (Utilidad por producto: ver limitación §11.)
14. Trazabilidad: de una bolsa vendida → lote tostado → proceso → pergamino → caficultor. El modelo de datos ya lo permite (cadena de FKs).

**Síntesis y razonamiento**
15. Resúmenes ejecutivos multi-dominio ("¿cómo va el negocio?").
16. Explicaciones causales acotadas ("¿por qué fue la mejor feria?" → el modelo compara ventas, ticket, gastos, mix de productos y argumenta).
17. Insights proactivos dentro de la respuesta ("además, nota que el 60% de la venta de Innovo fue un solo producto").
18. Recomendaciones operativas ("llevar más stock de X a la próxima feria, porque se agotó en las últimas 2").

**Futuras (§8)**
19. Proyecciones simples (ventas próximas N semanas), simulaciones "qué pasaría si", gráficos conversacionales, reportes PDF, alertas programadas.

---

## 5. Memoria conversacional

### 5.1 Tres niveles de memoria

**Nivel 1 — Historial literal (ventana deslizante).** Los últimos K turnos (sugerido: 10–15 mensajes) van completos al LLM, **incluyendo las llamadas a tools y sus resultados resumidos**. Esto resuelve naturalmente el encadenamiento del ejemplo:

> "¿Cuál fue la mejor feria?" → el resultado de `listar_ferias` (Innovo, $X) queda en el historial.
> "¿Y el producto más vendido allí?" → el modelo ve en el historial que "allí" = Innovo (id 4) y llama `ventas_feria(fair_id=4, ...)` sin volver a resolver nada.
> "¿Y cuál dejó mayor utilidad?" → mismo contexto, cambia la métrica.

**Nivel 2 — Pizarra de entidades (slots).** Estructura pequeña mantenida por el backend y anexada al contexto en cada turno:

```
Contexto activo: feria=Innovo(4) · producto=Bourbon 250g(12) · periodo=2026-Q1 · cliente=—
```

Se actualiza tras cada turno con las entidades que las tools resolvieron. Su función: sobrevivir a la ventana deslizante — si la conversación es larga y el turno donde se resolvió "Innovo" ya salió de la ventana, la pizarra sigue diciendo cuál es "esa feria". Cuesta ~30 tokens y elimina la clase de error más común en conversaciones largas.

**Nivel 3 — Resumen acumulado.** Cuando el historial excede la ventana, los turnos que salen se comprimen en un párrafo de resumen (generado por el mismo LLM en una llamada barata al cierre del turno, o de forma perezosa al turno siguiente). El contexto enviado siempre es: `system + resumen + pizarra + últimos K turnos + mensaje nuevo` — tamaño acotado sin importar la duración de la conversación.

### 5.2 Qué se persiste en PostgreSQL

- `chat_conversations`: id, user_id, título (autogenerado), created_at.
- `chat_messages`: conversación, rol (user | assistant | tool), contenido, tool_name/args/result (JSON), tokens de entrada/salida, latencia.
- El resumen acumulado y la pizarra de entidades, como columnas de la conversación (se sobreescriben).

Persistir los tool calls no es opcional: es la herramienta de debugging y de evaluación de calidad (§10) más valiosa que se tendrá.

### 5.3 Qué NO conservar

- Resultados grandes de tools de turnos viejos: en el historial se guardan completos en DB, pero al re-enviar al LLM los resultados de turnos anteriores pueden truncarse a su `resumen` (los detalles ya fueron usados para redactar aquella respuesta).
- Memoria entre conversaciones distintas: fuera de alcance en fase 1. Si se quisiera ("el usuario siempre pregunta por Innovo"), sería una fase futura con memoria de usuario explícita.

---

## 6. Pipeline de razonamiento

Un matiz importante frente al planteamiento inicial: no conviene implementar los pasos 1–4 (intención, entidades, referencias, plan) como etapas programáticas separadas con llamadas distintas al LLM. Los modelos actuales con tool use hacen ese razonamiento **dentro del propio loop de tool calling**, mejor y más barato que un pipeline de clasificadores encadenados. El pipeline correcto es un **loop con barandillas**:

```
1. PREPARAR      Backend arma contexto: system + resumen + pizarra + ventana + mensaje.
2. RAZONAR       LLM interpreta intención y referencias ("esa feria" → pizarra/historial).
                 │
3. RESOLVER      ├─ Si hay nombres no resueltos → tool resolver_entidad.
                 │   · 1 candidato claro → continúa.
                 │   · varios candidatos → PREGUNTA al usuario (respuesta corta, sin adivinar).
                 │   · 0 candidatos → informa y sugiere cercanos.
                 │
4. EJECUTAR      ├─ LLM llama 1..n tools de dominio/análisis (paralelas si son independientes).
                 │   Backend: valida parámetros (JSON Schema) → ejecuta → responde JSON compacto.
                 │   Error de parámetros → mensaje de error accionable → el LLM se autocorrige.
                 │
5. VALIDAR       ├─ Backend adjunta metadatos a cada resultado: num_registros, periodo real
                 │   cubierto, advertencias ("sin datos en ese rango"). El LLM valida contra
                 │   la pregunta: ¿cubre el periodo?, ¿la entidad es la correcta?
                 │
6. ITERAR        ├─ ¿Falta información para responder? → vuelve a 4 (máx. 6–8 iteraciones,
                 │   límite duro del backend; al tocarlo, el modelo responde con lo que tenga
                 │   y lo dice explícitamente).
                 │
7. SINTETIZAR    └─ Respuesta final en lenguaje natural: dato → comparación → conclusión.
                     Reglas del system prompt: citar cifras exactamente como llegaron de las
                     tools, declarar supuestos ("asumí marzo 2026"), nunca inventar números.
8. CERRAR        Backend persiste turno, actualiza pizarra y resumen, registra tokens/latencia.
```

Las "barandillas" programáticas del backend (no del modelo): validación de schema, límite de iteraciones, timeout por tool, tope de filas por respuesta, y la regla de desambiguación del paso 3. Todo lo demás es criterio del modelo — ahí está su valor.

---

## 7. Estrategia de consumo de tokens

El costo por turno es: `system prompt + definiciones de tools + memoria + resultados de tools + respuesta`. Estrategias, ordenadas por impacto:

1. **Agregación previa en Pandas (la más importante).** Ninguna tool devuelve filas crudas; devuelven agregados con `top` acotado (default 10, máximo duro 50 filas). Una pregunta sobre 10.000 ventas cuesta lo mismo que sobre 100: el DataFrame se reduce en el servidor. Esta sola decisión es la diferencia entre un sistema viable y uno incosteable.
2. **Formato de respuesta compacto.** Los resultados de tools van como JSON plano con claves cortas, sin campos nulos ni metadatos ORM; números redondeados a la precisión útil (2 decimales en dinero, 1 en porcentajes). Una tabla de 10 filas × 4 columnas ≈ 150–250 tokens.
3. **Tool calling iterativo en lugar de precarga.** No se envía "contexto de negocio" masivo por si acaso: el modelo pide exactamente lo que necesita, cuando lo necesita. `obtener_esquema_negocio` existe justamente para sacar el diccionario del dominio del system prompt.
4. **Ventana + resumen + pizarra (§5).** Contexto conversacional de tamaño acotado, O(1) respecto a la longitud de la conversación.
5. **Truncado de resultados históricos.** Los resultados de tools de turnos pasados se re-envían truncados a su campo `resumen`.
6. **Prompt caching.** El system prompt y las definiciones de tools son idénticos en cada llamada → marcarlos como cacheables (la API de Claude lo soporta explícitamente). El bloque fijo (~4–5k tokens) pasa a costar ~10% en llamadas subsecuentes. Ordenar el prompt con lo estático primero.
7. **Doble tope defensivo.** El backend impone `top ≤ 50` y trunca cualquier respuesta de tool que exceda ~2k tokens (con aviso `"truncado": true` para que el modelo sepa pedir más fino). Protege contra el caso en que el modelo pida algo desproporcionado.
8. **Modelo escalonado (opcional, fase 3+).** Turnos triviales de seguimiento podrían atenderse con un modelo más barato; no es necesario al inicio — primero medir con los tokens registrados en `chat_messages`.

Estimación de orden de magnitud por turno típico: 4–5k fijos (mayormente cacheados) + 1–2k de memoria + 0.3–1k de resultados de tools + 0.3–0.8k de respuesta ≈ **manejable incluso con decenas de consultas diarias**.

---

## 8. Escalabilidad futura

La arquitectura queda preparada porque tiene tres costuras de extensión limpias:

1. **Nuevas tools** se registran en el ToolRegistry sin tocar el orquestador. Proyecciones (`proyectar(dominio, metrica, horizonte)` con media móvil o Holt-Winters en Pandas/statsmodels) y simulaciones ("¿qué pasaría si subo el precio 10%?" → tool que recalcula sobre el histórico con el supuesto) son solo tools nuevas.
2. **Respuestas estructuradas, no solo texto.** Desde fase 1, el mensaje del asistente se persiste y transmite como lista de **bloques**: `texto`, y en el futuro `tabla`, `grafico` (spec JSON tipo {tipo: barras, series, ejes} que el frontend renderiza con Recharts o similar), `descarga`. Los gráficos conversacionales y dashboards no requieren rediseño: son un tipo de bloque nuevo que una tool (`generar_grafico`) produce a partir de datos ya agregados. **Esta decisión hay que tomarla ahora aunque los gráficos lleguen después** — cambiar de "string" a "bloques" a posteriori es una migración molesta de API y frontend.
3. **Los AnalyticsServices son independientes del chat.** La capa de agregados sirve igual para: reportes PDF (una plantilla que consume los mismos agregados + WeasyPrint/reportlab), exportaciones a Excel, alertas programadas (un scheduler que evalúa las mismas funciones — "avísame si el stock de X baja de N" — y no necesita al LLM para evaluar la condición, solo opcionalmente para redactar el aviso), y futuros endpoints del dashboard. El chatbot es *un* consumidor de esa capa, no su dueño.

Además: la interfaz con el LLM se encapsula detrás de un puerto propio (`LLMClient`), de modo que cambiar de proveedor o versión de modelo no toque tools ni orquestador.

---

## 9. Riesgos técnicos y mitigaciones

| Riesgo | Descripción | Mitigación |
|---|---|---|
| Alucinación de cifras | El modelo "redondea creativo" o inventa un número no presente en los resultados | Regla dura en system prompt: toda cifra debe provenir de un resultado de tool; los resultados persistidos permiten auditar; en respuestas críticas, incluir la fuente ("según ventas de feria del 3–5 marzo") |
| Ambigüedad de entidades | "Feria de marzo" matchea 2 ferias; "Juan" matchea 3 clientes | `resolver_entidad` devuelve candidatos y el pipeline obliga a preguntar si hay >1 plausible; nunca escoger en silencio |
| Respuestas inconsistentes | La misma pregunta da números distintos en días distintos por rutas de tools diferentes | Definiciones canónicas únicas en AnalyticsService (una sola función calcula "total de ventas"); las tools de análisis reutilizan las de dominio, no reimplementan; suite de preguntas doradas (§10) como regresión |
| Loop infinito / iteraciones excesivas | El modelo encadena tools sin converger | Tope duro de 6–8 iteraciones + timeout global por turno (~60 s); al tocarlo, responde con lo disponible declarándolo |
| Consultas costosas | Agregación sobre años de datos en tablas grandes | Filtros SIEMPRE en SQL (fechas/ids) antes de materializar el DataFrame; los índices ya existentes (`idx_sale_date`, `idx_fair_start`, etc.) cubren los accesos; límite de rango por defecto (p. ej. 24 meses) salvo petición explícita; `statement_timeout` en la sesión de solo lectura |
| Tools demasiado grandes o pequeñas | Ver §3 | Regla de granularidad media; revisar el registro de tool calls: si una tool casi nunca se usa o siempre se usa en el mismo par, re-cortar |
| Contexto conversacional corrupto | Referencia resuelta a la entidad equivocada ("allí" ≠ Innovo) | Pizarra de entidades explícita y visible; la respuesta nombra siempre la entidad ("En **Innovo**, el producto más vendido…") para que el usuario detecte el error al instante |
| Consumo excesivo de tokens | Conversaciones largas o resultados grandes | §7 completo; tokens por turno registrados en `chat_messages` → alertar si un turno excede umbral |
| Latencia alta | 3–4 llamadas al LLM en serie por turno | Streaming SSE desde el primer token de la respuesta final + indicador de progreso por tool ("consultando ventas de Innovo…"); tools independientes en paralelo; prompt caching también reduce latencia |
| Seguridad / permisos | El chat expone datos que el rol del usuario no debería ver | El ChatService corre con el `current_user` real; si mañana se restringen costos a admin, la restricción se aplica en el AnalyticsService (una sola vez), no en el prompt |
| Escritura accidental | Una tool que modifique datos | Fase 1–3: **todas las tools son de solo lectura** y usan una sesión de DB de solo lectura. Acciones de escritura, si algún día se quieren, serían tools separadas con confirmación explícita del usuario |

---

## 10. Plan de implementación por fases

### Fase 0 — Fundaciones (sin LLM)
**Construir:** capa `analytics/` con 4–5 funciones núcleo (ventas agregadas, reporte de feria, estado de inventario, procesos agregados) devolviendo JSON compacto; probarlas con tests unitarios contra datos reales del Excel importado.
**Validar:** que los números coinciden con lo que el dashboard y el reporte de feria ya muestran (fuente canónica única).
**Criterio de avance:** agregados correctos y rápidos (<500 ms) sobre el volumen real.

### Fase 1 — Agente mínimo viable
**Construir:** módulo `chat/` (router/service/schema + 2 tablas), orquestador con loop de tool calling, ToolRegistry, `resolver_entidad` + 5–6 tools de dominio (consultar_ventas, listar_ferias, reporte_feria, estado_inventario, consultar_procesos), memoria = solo ventana deslizante, frontend `ChatPage` básica con streaming.
**Validar:** una **suite de ~30 preguntas doradas** con respuesta correcta conocida (calculada a mano o vía dashboard); medir exactitud, tokens y latencia por pregunta usando lo registrado en `chat_messages`.
**Criterio de avance:** ≥90% de las preguntas doradas de consulta directa correctas; cero cifras inventadas; latencia p50 < 10 s.

### Fase 2 — Contexto y comparaciones
**Construir:** pizarra de entidades + resumen acumulado; tools `comparar_entidades`, `comparar_periodos`, `ventas_feria`, `gastos_feria`, `analisis_clientes`; desambiguación interactiva; prompt caching.
**Validar:** conversaciones encadenadas de 5+ turnos con referencias ("esa feria", "el anterior"); ampliar la suite dorada con secuencias, no solo preguntas sueltas.
**Criterio de avance:** las secuencias de referencia se resuelven correctamente ≥90%; costo por turno estable en conversaciones largas.

### Fase 3 — Capacidades analíticas
**Construir:** `tendencia`, `detectar_anomalias`, `rotacion_inventario`, `analisis_rendimiento`, `resumen_ejecutivo`; afinar el system prompt para respuestas con estructura dato→comparación→conclusión. Resolver la definición de costo/utilidad (§11) y, si se aprueba, habilitar análisis de rentabilidad.
**Validar:** revisión humana de calidad de insights (¿las conclusiones son defendibles con los datos mostrados?); no solo exactitud numérica.
**Criterio de avance:** los usuarios reales (equipo Shaya) califican útiles ≥80% de los análisis; ninguna conclusión contradice los datos citados.

### Fase 4 — Extensiones
**Construir:** bloques de gráfico en la respuesta (frontend con Recharts), exportación (Excel vía la skill de agregados, PDF de resumen ejecutivo), proyecciones simples, y evaluación de alertas programadas sobre la capa analytics.
**Validar:** cada extensión contra usuarios reales antes de la siguiente.

Transversal a todas las fases: el registro de tool calls y tokens en `chat_messages` es el sistema de evaluación — revisarlo semanalmente para detectar tools mal usadas, preguntas que fallan y costos anómalos.

---

## 11. Observaciones críticas al planteamiento inicial

1. **"Utilidad" no es calculable hoy con precisión — es un vacío del modelo de datos, no del chatbot.** `Product` no tiene costo; `FairInventory.unit_value` y `FairSale.unit_value` son precios de venta. El costo real de una bolsa se deriva de la cadena `DetailProcess.unit_value` (costo de maquila por presentación) + costo proporcional del pergamino (`Parchment.purchase_price`). Antes de la fase 3 hay que **definir contablemente** cómo se computa el costo unitario (¿solo maquila?, ¿maquila + pergamino prorrateado por rendimiento?, ¿incluye merma?) y materializarlo en la capa analytics. Si no se hace, el chatbot responderá "utilidad" usando solo ingresos−gastos de feria, y eso debe declararse explícitamente en la respuesta para no engañar. Recomendación: fase 1–2 hablan de "ingresos" y "neto de feria"; "utilidad por producto" se habilita solo cuando el costo esté definido.
2. **No sobre-ingenierizar el pipeline de intención.** El planteamiento original (clasificar intención → extraer entidades → resolver referencias como etapas separadas) era el estado del arte pre-tool-use. Hoy es más robusto y barato dejar ese razonamiento dentro del loop del modelo con barandillas programáticas (§6). Menos código, menos puntos de fallo, mejor manejo de casos raros.
3. **Diseñar la respuesta como bloques desde el día 1** (§8.2), aunque la fase 1 solo emita bloques de texto. Es la decisión de API más barata de tomar ahora y más cara de tomar después.
4. **La capa analytics debe nacer independiente del chat** (§8.3). Es el activo de largo plazo del proyecto: dashboard, reportes, alertas y chatbot consumen las mismas definiciones canónicas de métricas — es también la mitigación estructural del riesgo de inconsistencia.
5. **Pandas es adecuado pero no siempre necesario.** Para agregados simples (sumas, conteos por grupo) SQL puro vía SQLAlchemy es más eficiente; Pandas aporta valor real en pivotes, series temporales, z-scores, correlaciones y RFM. Regla: filtrar y pre-agregar en SQL, análisis estadístico en Pandas. "Todo en Pandas" cargaría filas innecesarias a memoria.
