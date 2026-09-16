# Farm Operations — Dashboards y Alertas

> Documento 5 de la hoja de ruta ([arquitectura.md](arquitectura.md) §12).
> Basado en el modelo de datos, la API y el diseño ML aprobados.
> Estado: **✅ aprobado** (2026-09-16) — no se ha escrito código.
> Última actualización: 2026-09-16

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

`farm_id` es opcional: sin él, admin ve el agregado global y farmer el
agregado de sus fincas. `from`/`to` default: últimos 12 meses.

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

### 3.2 Gráficas de producción (`/production`)

Todas devuelven `BarChartData` para reutilizar los componentes existentes.

| Gráfica | Tipo (Recharts) | labels | series |
|---|---|---|---|
| Producción mensual | barras agrupadas | meses del rango | `cereza_kg`, `pergamino_kg` |
| Producción por finca (admin) / por lote (farmer) | barras horizontales | fincas o lotes | `pergamino_kg` |
| Rendimiento por lote | barras + línea de referencia (histórico de la finca) | lotes | `rendimiento_pct` |
| Producción por variedad | dona | variedades | `pergamino_kg` |
| Costo de recolección por kg | línea | meses | `cop_por_kg_cereza` (Σ pagos / Σ kg) |
| Pipeline de proceso | barras apiladas (una barra) | — | `en_beneficio_kg`, `en_secado_kg`, `guardado_kg`, `en_inventario_kg` |

### 3.3 Gráficas de calidad y sanidad (`/quality`)

| Gráfica | Tipo | labels | series |
|---|---|---|---|
| Distribución de puntajes | histograma (barras) | rangos de 2 puntos (70–72, 72–74…) | `secados` |
| Puntaje promedio por variedad | barras | variedades | `score_avg` |
| Puntaje y defectos por lote | barras agrupadas | lotes | `score_avg`, `defects_avg` |
| Evolución de calidad | línea | meses | `score_avg` |
| **Broca por lote** (último muestreo) | barras con línea de umbral (`broca_alert_pct` resuelto) | lotes | `broca_pct` |
| Roya por lote (último muestreo) | barras | lotes | `roya_pct` |
| Humedad final de secados | dispersión / barras con banda 10–12 % | secados del periodo | `humidity_pct` |

### 3.4 Widgets propios del farmer

Además de lo anterior, restringido a sus fincas:

- **Estado de mis ciclos**: tabla — lote, ciclo N, días desde inicio, última
  labor registrada (tipo + fecha), próxima cosecha estimada (§5), nº de
  alertas.
- **Recordatorios de labores**: la lista de alertas tipo *recordatorio*
  (§4.1) como checklist visual — no accionable, solo informativa.
- **Proyección de calidad** (ML): por lote activo, las 4 variables +
  `completeness` + descargo, con enlace al detalle (`/quality-projection`).

### 3.5 Widgets propios del admin

- **Selector de finca** (global / una finca) que re-filtra todo el dashboard.
- **Ranking de fincas**: rendimiento, puntaje promedio, alertas activas.
- **Mapa de sanidad**: tabla finca × (broca %, roya %) coloreada por umbral.
- **Café por entrar a inventario**: secados `completed` con `destination =
  stored`, para planear compras/ingresos.

## 4. Catálogo de alertas

Cada alerta define: **condición** (query), **parámetro** (columna de
`alert_configs` que la gobierna), **default del sistema**, **severidad** y
**mensaje**. Todas se calculan en `services/alerts.py` (§6).

Formato de salida (API §4):

```json
{
  "type": "drying_too_long",
  "severity": "high",
  "farm_id": 1, "plot_id": null, "entity": {"drying_id": 14},
  "message": "Secado #14 lleva 18 días (umbral 15)",
  "value": 18, "threshold": 15, "since": "2026-08-29"
}
```

Severidades: `info` (recordatorio), `medium` (desvío), `high` (riesgo de
pérdida o dato crítico faltante).

### 4.1 Recordatorios de labores (severidad `info`)

Se disparan cuando pasaron más de N días desde la **última labor de ese tipo
en el ciclo activo** (o desde el inicio del ciclo si no hay ninguna).

| Tipo | Parámetro | Default | Base del default |
|---|---|---|---|
| `fertilization_due` | `fertilization_reminder_days` | 120 | Práctica común: 2–3 fertilizaciones edáficas al año según régimen de lluvias → ~cada 4 meses. |
| `phytosanitary_due` | `phytosanitary_reminder_days` | 30 | El MIB de broca recomienda **muestreo mensual**; el recordatorio empuja a monitorear, no a aplicar. |
| `weeding_due` | `weeding_reminder_days` | 75 | Plateo/deshierba cada 2–3 meses en cafetales en producción. |
| `irrigation_due` | `irrigation_reminder_days` | **null (desactivado)** | La mayoría del café colombiano es de secano; solo se activa si la finca lo configura. |
| `harvest_pass_due` | `harvest_reminder_days` | 15 | En temporada, las pasadas de recolección se hacen cada 2–3 semanas. Solo aplica si hay una cosecha cerrada en el ciclo hace más de N días **y** el ciclo sigue activo. |

Un parámetro en `null` a nivel resuelto = recordatorio desactivado.

### 4.2 Alertas de desvío (severidad `medium`)

| Tipo | Condición | Parámetro | Default | Base |
|---|---|---|---|---|
| `cycle_inactive` | Ciclo `active` sin ningún registro (labor, clima, monitoreo, cosecha) en N días | `inactivity_alert_days` | 45 | Un cafetal en producción genera alguna actividad al menos mensualmente. |
| `humidity_out_of_range` | Secado `completed` con `final_humidity_pct` fuera de [min, max] | `min_final_humidity`, `max_final_humidity` | 10 / 12 | Rango de recibo estándar del pergamino seco en Colombia. |
| `fermentation_out_of_range` | Beneficio con horas de fermentación fuera de [min, max] | `min_fermentation_hours`, `max_fermentation_hours` | 10 / 24 | Ventana óptima ≈ 12–18 h a 20 °C; los límites de alerta son más amplios que el óptimo para no alarmar por variación normal de temperatura. |
| `harvest_without_quality` | Cosecha `closed` sin `quality_evals` etapa `cherry` | — | siempre | Dato crítico para trazabilidad y ML. |
| `drying_without_quality` | Secado `completed` sin `quality_evals` etapa `parchment` hace > 7 días | — | 7 | Idem; se da margen para la evaluación. |
| `yield_below_history` | Rendimiento del secado < histórico de la finca − 3 puntos | — | 3 pp | Desvío que suele indicar mal despulpado, café verde o pérdida (F2: referencia = histórico calculado). |

### 4.3 Alertas de riesgo (severidad `high`)

| Tipo | Condición | Parámetro | Default | Base |
|---|---|---|---|---|
| `broca_above_threshold` | Último `pest_monitorings.broca_pct` del ciclo ≥ umbral | `broca_alert_pct` | 2 % | Umbral de acción del MIB (Cenicafé). **No confundir** con la inflexión de calidad del generador ML (≈ 4 %, otra cantidad). |
| `drying_too_long` | Secado `in_progress` con `hoy − start_date` > N | `max_drying_days` | 15 | Marquesina/elba: 8–15 días; más tiempo con lluvia → riesgo de moho y fermento. |
| `processing_stalled` | Beneficio `in_progress` con fermentación iniciada hace > `max_fermentation_hours` y sin `fermentation_end` | `max_fermentation_hours` | 24 | Sobrefermentación en curso — es la única alerta "en tiempo real" del sistema. |
| `unpaid_labor` | Pagos pendientes con > 15 días desde el trabajo | — | 15 | Deuda laboral acumulada. |
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
def compute_alerts(db, *, farm_ids: list[int]) -> list[Alert]:
    configs = load_resolved_configs(db, farm_ids)   # 1 query fincas + 1 lotes
    alerts = []
    for check in CHECKS:          # una función por tipo de alerta
        alerts += check(db, farm_ids, configs)
    return sorted(alerts, key=severity_then_date)
```

- **Una función por tipo**, registrada en `CHECKS`; agregar una alerta nueva
  = agregar una función, sin tocar el resto.
- Cada función hace **una query agregada** por todas las fincas del scope
  (no un loop por lote): los índices `(crop_cycle_id, fecha)` y
  `idx_drying_status` del modelo de datos la soportan.
- Sin caché en v1. Si el panel llegara a sentirse lento, el primer paso es
  cachear el resultado 60 s por usuario en Redis (ya disponible en el
  compose), no persistir alertas.
- El mismo servicio alimenta el conteo de la tarjeta KPI y el panel: una sola
  llamada por carga de dashboard.

## 7. Frontend (lineamientos)

- Nueva feature `src/features/farm_dashboard/` siguiendo el patrón existente
  (`Page.tsx`, `models/types.ts`, `services/*.api.ts`, `mapper/*.ts`).
- Reutilizar los componentes de gráfica del `DashboardPage` actual: reciben
  `BarChartData`, así que los endpoints de §2 encajan sin adaptación.
- Panel de alertas: lista agrupada por severidad, cada ítem enlaza a la
  entidad (`/farm/plots/{id}`, `/farm/dryings/{id}`…). Sin botón "descartar"
  en v1 (A4: nada que persistir).
- Rol `farmer`: el dashboard de cultivo es su pantalla de inicio. Rol
  `admin`: entrada de menú "Cultivo" junto a las existentes.
- Vista móvil: las tarjetas KPI y el panel de alertas primero; las gráficas
  colapsadas. El farmer consulta desde el celular en la finca.
