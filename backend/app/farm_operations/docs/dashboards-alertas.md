# Farm Operations — Dashboards y Alertas

> Documento 5 de la hoja de ruta ([arquitectura.md](arquitectura.md) §12).
> Basado en el modelo de datos, la API y el diseño ML aprobados.
> Estado: **✅ aprobado** (2026-09-16). Implementados los valores por defecto
> y la resolución de umbrales por finca y lote (§4.4, bloque 1B), y el
> dashboard y el cálculo de alertas (§2–§7, bloque 6). La proyección de
> calidad (§3.4) llega con el modelo, en el bloque 7.
> Última actualización: 2026-10-03

---

## 1. Principios

1. **El sistema informa, nunca obliga** (arquitectura §7.2). Toda alerta es
   una notificación calculada; ignorarla no bloquea ninguna operación.
2. **Alertas calculadas al consultar, no persistidas** (API A4): sin tabla de
   alertas, sin jobs, sin estado que sincronizar. Con los volúmenes del
   sistema (cientos de lotes, no millones) la query es barata.
3. **Todo umbral es configurable** en dos niveles — lote → finca → default del
   sistema (G1). Los defaults de este documento son **valores iniciales
   razonables tomados de la práctica cafetera colombiana**, no verdades
   agronómicas: cada finca los ajusta.
4. **Reutilizar lo existente**: los widgets usan los mismos contratos
   (`BarChartData {labels, series}`, `ChartPoint`) y la misma librería
   (Recharts) que el dashboard actual de inventario/ventas.
5. **Mismo dashboard, distinto alcance**: admin y farmer ven la misma
   estructura de widgets; lo que cambia es el scoping de datos (admin → todas
   las fincas con selector; farmer → solo las suyas). Un solo frontend, sin
   duplicar componentes.

## 2. Endpoints (recordatorio de la API aprobada, §3.13)

| Endpoint | Devuelve | Widgets que alimenta |
|---|---|---|
| `GET /farm/dashboard/summary?farm_id=&from=&to=` | KPIs numéricos | Tarjetas §3.1 |
| `GET /farm/dashboard/alerts?farm_id=` | Lista de alertas activas | Panel de alertas §4 |
| `GET /farm/dashboard/production?farm_id=&from=&to=&group_by=` | `BarChartData` por serie | Gráficas de producción §3.2 |
| `GET /farm/dashboard/quality?farm_id=&from=&to=` | `BarChartData` por serie | Gráficas de calidad §3.3 |
| `GET /farm/dashboard/periods?farm_id=&plot_id=` | Rangos rápidos calculados (temporadas de cosecha) | Selector de periodo §2.1 |
| `GET /farm/dashboard/cycles?farm_id=` | Estado de los ciclos activos | Estado de mis ciclos §3.4 |
| `GET /farm/dashboard/farms?from=&to=` | Una fila por finca | Ranking y mapa de sanidad §3.5 |

`farm_id` es opcional: sin él, admin ve el agregado global y farmer el
agregado de sus fincas. `from`/`to` default: últimos 12 meses. En la API los
parámetros del periodo se llaman `date_from` y `date_to`, como en el resto
de los filtros de fecha del módulo.

Las gráficas «por unidad» (producción, rendimiento, puntaje y defectos,
broca y roya) van **por lote** cuando el alcance es una sola finca y **por
finca** cuando son varias; la respuesta dice cuál (`unit`). Lo que se
reparte entre lotes (pergamino, rendimiento, puntaje) se pondera por la
cereza que cada lote aportó a cada secado, con la misma proporción de la
trazabilidad.

### 2.1 Selector de periodo

Todo el dashboard se filtra por un **rango de fechas** que el usuario elige
de dos formas:

- **Rango personalizado**: dos selectores de fecha (`from`, `to`).
- **Botones rápidos**: *Este mes · Últimos 3 meses · Últimos 6 meses ·
  Último año · **Última cosecha** · **Últimas 2 cosechas** · **Últimas 3
  cosechas** · Todo.*

Los botones de calendario se resuelven en el frontend. Los de **cosecha** no:
una "cosecha" aquí es una **temporada** (la principal, la mitaca), no una
pasada individual, y sus fechas dependen de los datos. Por eso existe
`/dashboard/periods`, que las calcula:

- Una **temporada** = grupo de `harvests` del scope (finca, todas, o un lote)
  tal que entre una y la siguiente no pasan más de **45 días sin actividad de
  recolección** (constante `SEASON_GAP_DAYS`, en `services/`). Se calcula con
  una función de ventana sobre `harvests` ordenadas por `start_date`; con
  cientos de cosechas es instantáneo.
- Respuesta: lista de temporadas, la más reciente primero:
  `[{label: "Cosecha oct–dic 2025", from, to, harvests: 14, cherry_kg: 8420}, …]`.
- Una pasada abierta cuenta hasta su última recolección registrada, no hasta
  hoy: así una pasada que se olvidó cerrar no une dos temporadas. La
  temporada en curso (con una pasada abierta y recolección reciente) llega
  hasta hoy.
- "Últimas N cosechas" = `from` de la N-ésima más reciente → `to` de la más
  reciente. El frontend solo rellena `from`/`to` y llama a los demás
  endpoints — no hay lógica de temporadas duplicada en dos lados.
- A nivel de **lote**, una temporada coincide con la ventana de cosecha de un
  ciclo; a nivel de finca o global, agrupa las de todos los lotes que
  cosecharon en esas fechas.

**Qué obedece al periodo y qué no.** Los widgets *de periodo* (producción,
calidad, costos, rendimiento, puntaje promedio) usan el rango. Los widgets
*de estado* (ciclos activos, cosechas abiertas, café en beneficio/secado,
pergamino guardado, pagos pendientes, **alertas**) muestran siempre el
**ahora** — una alerta de secado no depende de qué mes estés mirando. Las
tarjetas KPI marcadas "(periodo)" en §3.1 son las primeras; el resto son las
segundas.

El último rango elegido se recuerda por navegador (`localStorage`, comodidad
por usuario; no se persiste en servidor).

## 3. Widgets

### 3.1 Tarjetas KPI (`/summary`)

| KPI | Cálculo | Fuente |
|---|---|---|
| Fincas activas / lotes activos | conteo `active` | `farms`, `plots` |
| Área sembrada por variedad | Σ `plots.area` agrupado por `variety` (solo activos) | `plots` |
| Ciclos activos | conteo `crop_cycles.status = active` | `crop_cycles` |
| Cosechas abiertas | conteo `harvests.status = open` | `harvests` |
| kg cereza cosechada (periodo) | Σ `harvests.total_cherry_kg` con `end_date` en rango | `harvests` |
| kg pergamino producido (periodo) | Σ `dryings.output_kg` con `end_date` en rango | `dryings` |
| **Rendimiento cereza → pergamino** (periodo) | `Σ output_kg / Σ cereza trazada` × 100 — cereza trazada = Σ de `wet_processing_inputs.cherry_kg` de los beneficios que alimentaron esos secados | pivotes (F2: calculado, nunca configurado) |
| Rendimiento vs histórico | mismo cálculo sobre los 12 meses previos → variación en puntos | idem |
| Café en beneficio | conteo + Σ kg de `wet_processings.status = in_progress`, con días desde creación | `wet_processings` |
| Café en secado | conteo + Σ kg húmedos de `dryings.status = in_progress`, con días desde `start_date` | `dryings` |
| Pergamino guardado en finca | Σ `output_kg` de secados `completed` con `destination = stored` | `dryings` |
| Pagos pendientes de recolección | Σ `harvest_works.total_value` con `paid = false` + Σ `day_labors.daily_value` con `paid = false` | `harvest_works`, `day_labors` |
| Costo de cosecha (periodo) | Σ `total_value` de trabajos en cosechas cerradas del periodo | `harvest_works` |
| Puntaje promedio (periodo) | AVG `quality_evals.score` etapa `parchment` en rango | `quality_evals` |
| Alertas activas | conteo por severidad | §4 |

En pantalla las tarjetas van en dos grupos, **Ahora** (estado) y **En el
periodo**, para que se lea de un vistazo cuáles cambian con el selector. La
respuesta incluye además `stored_dryings`: los 10 secados guardados en finca
más antiguos, que alimentan el widget «café por entrar a inventario» (§3.5).

### 3.2 Gráficas de producción (`/production`)

Todas devuelven `BarChartData` para reutilizar los componentes existentes.

| Gráfica | Tipo (Recharts) | labels | series |
|---|---|---|---|
| Producción mensual | barras agrupadas | meses del rango | `cereza_kg`, `pergamino_kg` |
| Pergamino por unidad | barras horizontales | lotes (una finca) o fincas (varias) | `pergamino_kg` |
| Rendimiento por unidad | barras + línea de referencia (rendimiento de los 12 meses previos al periodo) | lotes o fincas | `rendimiento_pct` |
| Producción por variedad | dona | variedades | `pergamino_kg` |
| Costo de recolección por kg | línea | meses | `cop_por_kg_cereza` (Σ pagos / Σ kg) |
| Pipeline de proceso | barras apiladas (una barra) | — | `en_beneficio_kg`, `en_secado_kg`, `guardado_kg`, `en_inventario_kg` |

Los nombres de las series llegan legibles («Cereza (kg)», «Pergamino seco
(kg)», «Rendimiento (%)»…), porque la gráfica los muestra tal cual en la
leyenda y el tooltip. El pipeline es un widget de estado: muestra el ahora
aunque viaje en la misma respuesta que las gráficas del periodo; «en
inventario» es el saldo de los pergaminos del inventario que salieron de
secados del alcance. Las barras de rendimiento ajustan su eje a los datos
(no arrancan en 0) para que se vean diferencias de pocos puntos.

### 3.3 Gráficas de calidad y sanidad (`/quality`)

| Gráfica | Tipo | labels | series |
|---|---|---|---|
| Distribución de puntajes | histograma (barras) | rangos de 2 puntos (70–72, 72–74…) | `secados` |
| Puntaje promedio por variedad | barras | variedades | `score_avg` |
| Puntaje y defectos por lote | barras agrupadas | lotes | `score_avg`, `defects_avg` |
| Evolución de calidad | línea | meses | `score_avg` |
| **Broca por lote** (último muestreo) | barras con línea de umbral (`broca_alert_pct` resuelto) | lotes | `broca_pct` |
| Roya por lote (último muestreo) | barras | lotes | `roya_pct` |
| Humedad final de secados | histograma con el rango resaltado | rangos de 0,5 puntos entre 8 y 14 % (más los extremos) | `secados` |

- Puntaje y defectos por unidad, y puntaje por variedad, se ponderan por la
  cereza que cada lote aportó a cada secado evaluado.
- Broca y roya: último muestreo de cada ciclo activo; por finca, el mayor de
  sus lotes (el que pide atención). La línea de umbral es el
  `broca_alert_pct` resuelto de cada lote o finca.
- Humedad: barras en verde dentro del rango resuelto y en ámbar fuera. Con
  una finca, el rango es el de la finca; con varias, el valor por defecto
  (cada finca puede tener el suyo y la gráfica solo pinta uno).

### 3.4 Widgets propios del farmer

Además de lo anterior, restringido a sus fincas:

- **Estado de mis ciclos** (`/cycles`): tabla — lote, ciclo N, días desde
  inicio, última labor registrada (tipo + fecha), estado de la cosecha
  (esperando / en cosecha / cosechado), próxima cosecha estimada (§5), nº de
  alertas del lote. El administrador también la ve al elegir una finca.
- **Recordatorios de labores**: la lista de alertas tipo *recordatorio*
  (§4.1) como checklist visual — no accionable, solo informativa.
- **Proyección de calidad** (ML): por lote activo, las 4 variables +
  `completeness` + descargo, con enlace al detalle (`/quality-projection`).
  Llega con el modelo (bloque 7).

### 3.5 Widgets propios del admin

- **Selector de finca** (global / una finca) que re-filtra todo el dashboard.
- **Ranking de fincas** y **mapa de sanidad** en una sola tabla (`/farms`):
  una fila por finca con lotes activos, cereza y pergamino del periodo,
  rendimiento, puntaje promedio, alertas por severidad, broca y roya
  coloreadas por umbral, y pergamino guardado. Al tocar una finca, el
  dashboard pasa a esa finca.
- **Café por entrar a inventario**: secados `completed` con `destination =
  stored`, los más antiguos primero, para planear compras/ingresos.

## 4. Catálogo de alertas

Cada alerta define: **condición** (query), **parámetro** (columna de
`alert_configs` que la gobierna), **default del sistema**, **severidad** y
**mensaje**. Todas se calculan en `services/alerts.py` (§6).

Formato de salida (API §4):

```json
{
  "type": "drying_too_long",
  "severity": "high",
  "farm_id": 1, "farm_name": "La Esperanza", "plot_id": null, "plot_name": null,
  "entity": {"drying_id": 14},
  "message": "Secado 14 lleva 18 días (umbral 15)",
  "value": 18, "threshold": 15, "since": "2026-08-29"
}
```

Severidades: `info` (recordatorio), `medium` (desvío), `high` (riesgo de
pérdida o dato crítico faltante).

**Ventana de las alertas sobre hechos cerrados.** Las alertas que miran algo
ya terminado (humedad, fermentación, cosecha o secado sin evaluar,
rendimiento bajo) solo cubren los **últimos 30 días** (`RECENT_DAYS`). Una
alerta es para actuar; lo que pasó hace meses es materia de los reportes y
llenaría el panel con historia que ya no tiene arreglo. Las alertas de
estado (secado largo, beneficio detenido, pasada abierta, broca, pagos,
recordatorios) no tienen ventana: valen mientras la situación siga.

### 4.1 Recordatorios de labores (severidad `info`)

Se disparan cuando pasaron más de N días desde la **última labor de ese tipo
en el ciclo activo** (o desde el inicio del ciclo si no hay ninguna).

| Tipo | Parámetro | Default | Base del default |
|---|---|---|---|
| `fertilization_due` | `fertilization_reminder_days` | 120 | Práctica común: 2–3 fertilizaciones edáficas al año según régimen de lluvias → ~cada 4 meses. |
| `phytosanitary_due` | `phytosanitary_reminder_days` | 30 | El MIB de broca recomienda **muestreo mensual**; el recordatorio empuja a monitorear, no a aplicar. Cuenta el último muestreo de plagas **o** la última aplicación fitosanitaria. |
| `weeding_due` | `weeding_reminder_days` | 75 | Plateo/deshierba cada 2–3 meses en cafetales en producción. Solo cuentan las labores culturales de tipo deshierba. |
| `irrigation_due` | `irrigation_reminder_days` | **null (desactivado)** | La mayoría del café colombiano es de secano; solo se activa si la finca lo configura. |
| `harvest_pass_due` | `harvest_reminder_days` | 15 | En temporada, las pasadas de recolección se hacen cada 2–3 semanas. Aplica si la última pasada del ciclo cerró hace más de N días, no hay otra abierta **y** el ciclo sigue activo; o, sin pasadas en el ciclo, si ya pasó la fecha estimada por la floración (§5). |

Un parámetro en `null` a nivel resuelto = recordatorio desactivado.

### 4.2 Alertas de desvío (severidad `medium`)

| Tipo | Condición | Parámetro | Default | Base |
|---|---|---|---|---|
| `cycle_inactive` | Ciclo `active` sin ningún registro (labor, clima, monitoreo, cosecha, recolección) en N días. El clima de la finca cuenta para todos sus lotes | `inactivity_alert_days` | 45 | Un cafetal en producción genera alguna actividad al menos mensualmente. |
| `humidity_out_of_range` | Secado `completed` en los últimos 30 días con `final_humidity_pct` fuera de [min, max] | `min_final_humidity`, `max_final_humidity` | 10 / 12 | Rango de recibo estándar del pergamino seco en Colombia. |
| `fermentation_out_of_range` | Beneficio con fermentación terminada en los últimos 30 días y horas fuera de [min, max] | `min_fermentation_hours`, `max_fermentation_hours` | 10 / 24 | Ventana óptima ≈ 12–18 h a 20 °C; los límites de alerta son más amplios que el óptimo para no alarmar por variación normal de temperatura. |
| `harvest_without_quality` | Cosecha cerrada en los últimos 30 días sin `quality_evals` etapa `cherry` | — | siempre | Dato crítico para trazabilidad y ML. |
| `drying_without_quality` | Secado cerrado hace entre 7 y 37 días sin `quality_evals` etapa `parchment` | — | 7 | Idem; se da margen para la evaluación y luego la misma ventana de 30 días. |
| `yield_below_history` | Secado cerrado en los últimos 30 días con rendimiento < histórico de la finca − 3 puntos. Histórico = pergamino / cereza trazada de los secados de la finca en los 365 días anteriores a esa ventana; con menos de 3 secados no hay referencia y no se alerta | — | 3 pp | Desvío que suele indicar mal despulpado, café verde o pérdida (F2: referencia = histórico calculado). |

### 4.3 Alertas de riesgo (severidad `high`)

| Tipo | Condición | Parámetro | Default | Base |
|---|---|---|---|---|
| `broca_above_threshold` | Último `pest_monitorings.broca_pct` del ciclo ≥ umbral | `broca_alert_pct` | 2 % | Umbral de acción del MIB (Cenicafé). **No confundir** con la inflexión de calidad del generador ML (≈ 4 %, otra cantidad). |
| `drying_too_long` | Secado `in_progress` con `hoy − start_date` > N | `max_drying_days` | 15 | Marquesina/elba: 8–15 días; más tiempo con lluvia → riesgo de moho y fermento. |
| `processing_stalled` | Beneficio `in_progress` con fermentación iniciada hace > `max_fermentation_hours` y sin `fermentation_end` | `max_fermentation_hours` | 24 | Sobrefermentación en curso — es la única alerta "en tiempo real" del sistema. |
| `unpaid_labor` | Pagos pendientes con > 15 días desde el trabajo (recolección y jornales). **Una alerta por finca** con el número de pagos, el total y la fecha del más antiguo | — | 15 | Deuda laboral acumulada; una alerta por trabajo inundaría el panel. |
| `harvest_open_too_long` | Cosecha `open` hace > 30 días | — | 30 | Una pasada no dura un mes; probablemente se olvidó cerrarla (afecta balance de masas). |

### 4.4 Resolución de umbrales

Para cada lote: `plot_config.X ?? farm_config.X ?? DEFAULTS.X`, donde
`DEFAULTS` es un dict en `services/alerts.py` con los valores de las tablas
anteriores (única fuente; el endpoint `/alert-configs/resolved/plot/{id}`
lo expone con el origen de cada valor). Las alertas de secado/beneficio, que
no tienen lote único (mezclas), resuelven a nivel **finca**.

## 5. Proyección de cosecha por floración

Widget "próxima cosecha estimada" en el estado de ciclos del farmer:

- `fecha_estimada = fecha de la floración principal del ciclo + 224 días`
  (≈ 32 semanas), rango ± 14 días.
- Floración principal = la de mayor `intensity` del ciclo; si hay varias
  `high`, la primera.
- Sin floración registrada → el widget muestra "registra la floración para
  estimar la cosecha" (incentivo de captura, no alerta).
- Alimenta `harvest_pass_due`: si la fecha estimada ya pasó y no hay cosecha
  abierta ni cerrada en el ciclo → recordatorio `info`.

## 6. Diseño de `services/alerts.py`

```python
def compute_alerts(db, farm_ids, today=None, now=None) -> list[Alert]:
    ctx = build_context(db, farm_ids, today, now)   # nombres + configs de fincas y lotes
    alerts = []
    for check in CHECKS:          # una función por tipo de alerta
        alerts += check(ctx)
    return sorted(alerts, key=severidad_luego_fecha)
```

- **Una función por tipo**, registrada en `CHECKS`; agregar una alerta nueva
  = agregar una función, sin tocar el resto.
- `Context` lleva la sesión, el alcance, la fecha y la hora de referencia y
  las configuraciones ya cargadas; resuelve umbrales por lote
  (`plot_value`) o por finca (`farm_value`). `today` y `now` se pueden
  inyectar: las pruebas fijan la fecha y el generador sintético revisa las
  alertas en fechas del pasado.
- Las temporadas del selector (§2.1) viven en `services/seasons.py`, sin
  FastAPI, junto a `services/alerts.py`.
- Cada función hace **una query agregada** por todas las fincas del scope
  (no un loop por lote): los índices `(crop_cycle_id, fecha)` y
  `idx_drying_status` del modelo de datos la soportan.
- Sin caché en v1. Si el panel llegara a sentirse lento, el primer paso es
  cachear el resultado 60 s por usuario en Redis (ya disponible en el
  compose), no persistir alertas.
- El mismo servicio alimenta el conteo de la tarjeta KPI y el panel: una sola
  llamada por carga de dashboard. El estado de los ciclos y el ranking de
  fincas también lo reutilizan para contar alertas por lote y por finca.
- Con los datos sintéticos (12 fincas, 4 años) cada endpoint responde en
  menos de 100 ms.

## 7. Frontend

- El dashboard vive dentro del módulo, en
  `src/features/farm_operations/dashboard/`, y no en una feature aparte:
  comparte las rutas, los componentes de interfaz, los formatos y el
  cargador de datos del resto de pantallas de cultivo. Los tipos van en
  `models/types.ts` y las llamadas en `services/dashboard.api.ts`, como en
  el resto del módulo.
- Las piezas de gráfica que eran privadas de `DashboardPage.tsx` se
  extrajeron a `src/components/charts/` sin cambio visual (`chartData.ts`,
  `GlobalChartDefs`, `CustomTooltip`, `DonutChart`, `KpiCard`, `ChartCard`).
  El dashboard de inventario y ventas y el de cultivo las comparten; el de
  cultivo añade `FarmChart`, que sobre el mismo contrato `BarChartData`
  dibuja barras verticales u horizontales, apiladas, líneas de umbral, eje
  derecho y línea de referencia.
- Rutas: la pestaña **Resumen** es `/cultivo` (el dashboard) y la lista de
  fincas pasó a `/cultivo/fincas`. Rol `farmer`: `/cultivo` es su pantalla
  de inicio. Rol `admin`: la entrada de menú «Cultivo» abre el resumen.
- Panel de alertas: riesgos y desvíos agrupados por severidad, y los
  recordatorios en una tarjeta aparte; 6 visibles por grupo y «Ver las N»
  para el resto. Cada ítem enlaza a su entidad: cosecha
  (`/cultivo/cosechas/{id}`), secado (`/cultivo/secados/{id}`), beneficio
  (`/cultivo/beneficios/{id}`), lote (`/cultivo/lotes/{id}`) o pagos de la
  finca (`/cultivo/fincas/{id}/pagos`). Sin botón "descartar" en v1 (A4:
  nada que persistir).
- Vista móvil: el panel de alertas primero, luego las tarjetas KPI; las
  gráficas colapsadas por debajo de 1024 px. El farmer consulta desde el
  celular en la finca.
