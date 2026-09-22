# Farm Operations — Especificación de API

> Documento 3 de la hoja de ruta ([arquitectura.md](arquitectura.md) §12).
> Basado en el modelo de datos aprobado ([modelo-datos.md](modelo-datos.md)).
> Estado: **✅ aprobado** (2026-08-06) — no se ha escrito código.
> Última actualización: 2026-08-06

---

## 1. Convenciones

Heredadas de la API existente:

| Convención | Regla |
|---|---|
| Montaje | Todo bajo `/api/v1/farm` — una línea en `api_v1.py`: `include_router(farm_router, prefix="/farm", tags=["farm"])`. |
| Estilo de rutas | Verbos como en el resto del sistema: `/create`, `/get`, `/get/{id}`, `/update/{id}`, `/delete/{id}`. Operaciones de negocio como acción sobre el recurso: `/{id}/close`, `/{id}/reopen`, `/{id}/complete`. |
| Autenticación | Cookie `access_token` + `get_current_user` (igual que todo el sistema). |
| Estructura | `app/farm_operations/api/v1/<recurso>/` con `router.py`, `schema.py`, `service.py` (patrón `farmers/`). |
| Respuestas | `response_model` Pydantic por endpoint; listas como `List[XResponse]`; borrados devuelven `{"message": ...}`. |
| Unidades | La API **solo habla en kg** (F1). La conversión arrobas/cargas → kg es responsabilidad del frontend. |
| Fechas | `date` ISO (`2026-08-06`); instantes `datetime` ISO con zona. |

### Errores

| Código | Cuándo |
|---|---|
| 401 | Sin cookie o token inválido. |
| 403 | Rol sin permiso o finca que no pertenece al farmer. |
| 404 | Recurso inexistente **o fuera del alcance del usuario** (no se revela existencia de datos ajenos). |
| 409 | Conflicto de estado: cerrar lo ya cerrado, abrir segundo ciclo activo, exceder balance de masas. |
| 422 | Validación Pydantic (rangos, campos obligatorios por etapa/enum `other`). |

## 2. Permisos

### Dependencias nuevas (en `app/farm_operations/api/v1/dependencies.py`)

| Dependencia | Comportamiento |
|---|---|
| `require_farm_role` | Pasa si `role in ('admin', 'farmer')`; 403 para `user` (personal de Shaya no opera cultivo en v1). |
| `get_accessible_farm(farm_id)` | `admin` → cualquier finca. `farmer` → la finca solo si `farm.farmer.person_id == current_user.person_id`; si no, 404. |
| Scoping de listas | Los `GET /get` sin `farm_id` devuelven: `admin` → todo (filtrable), `farmer` → solo sus fincas. Automático en el service. |

Todo recurso anidado (lote, ciclo, cosecha, secado…) resuelve su finca raíz y
aplica `get_accessible_farm`. Los catálogos (`supplies`) son globales: lectura
para cualquier autenticado del módulo, escritura también (creación al vuelo,
D7), borrado solo `admin`.

### Módulos existentes y rol `farmer`

El rol `farmer` corresponde a usuarios externos: no accede a ningún módulo de
Shaya (plan de implementación, 2.1 y 2.2).

| Regla | Implementación |
|---|---|
| Módulos existentes solo para personal | `require_staff` (lista explícita: `admin`, `user`; todo lo demás se rechaza) aplicada en cada `include_router` de `api_v1.py`, salvo `auth`. Un farmer recibe 403. |
| Asistente | El chatbot rechaza el rol `farmer` (403). |
| Auditoría | Un test recorre todas las rutas registradas y exige 403 para una sesión farmer fuera de `/farm` y `/auth`. |
| `UserRole` | Incluye `farmer` para lectura (listados de usuarios); `/users/create` sigue aceptando solo roles de personal. Las cuentas farmer se crean únicamente con `/farmer-accounts/*` (§3.12), que enlazan la `Person` existente. |

### Matriz resumen

| Recurso | farmer | admin |
|---|---|---|
| Módulos de Shaya (ventas, inventario, gastos…) | — (403) | según permisos actuales |
| Sus fincas y todo lo colgado de ellas | CRUD | CRUD |
| Fincas de otros | — (404) | CRUD |
| `supplies` (catálogo global) | crear, leer, editar | + eliminar/desactivar |
| Cuentas de caficultor | — | crear (E2) |
| Dashboard | el suyo | global |
| Proyección ML | sus lotes | todos |

## 3. Endpoints

Prefijo común: `/api/v1/farm`. Todos con auth; columna **Rol** indica el
mínimo (`farm` = `require_farm_role` + scoping de finca).

### 3.1 `farms`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/farms/create` | farm | Crea finca. `farmer_id` obligatorio: `admin` indica cualquiera; `farmer` solo el suyo (se valida). |
| GET | `/farms/get` | farm | Lista con scoping. Filtros: `search`, `active`. |
| GET | `/farms/get/{id}` | farm | Detalle + conteo de lotes activos. |
| PUT | `/farms/update/{id}` | farm | |
| DELETE | `/farms/delete/{id}` | farm | Solo sin lotes (RESTRICT). |

### 3.2 `plots` (+ eventos y ciclo de vida)

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/plots/create` | farm | Crea lote (terreno + siembra). Si trae `renewed_from_plot_id`, el service valida que el anterior esté `closed` y pertenezca a la misma finca. |
| GET | `/plots/get` | farm | Filtros: `farm_id`, `status`, `variety`. |
| GET | `/plots/get/{id}` | farm | Detalle + ciclo activo + edad efectiva calculada. |
| GET | `/plots/get/{id}/renewal-defaults` | farm | Datos del terreno del lote para precargar el formulario del lote nuevo (renovación). |
| PUT | `/plots/update/{id}` | farm | |
| POST | `/plots/{id}/close` | farm | Cierre definitivo (D2): exige sin ciclo activo; registra `plot_event(closure)` y `closed_at`. |
| POST | `/plots/{id}/reopen` | farm | Solo corrección de error: registra `plot_event(reopening)`. |
| DELETE | `/plots/delete/{id}` | farm | Solo sin ciclos (RESTRICT). |
| POST | `/plots/{id}/events/create` | farm | Evento manual: `zoca`, `partial_replant`, `shade_change`, `other` (+`other_detail`). `closure`/`reopening` solo vía close/reopen. |
| GET | `/plots/{id}/events/get` | farm | Historial de eventos. |

### 3.3 `alert-configs`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| PUT | `/alert-configs/farm/{farm_id}` | farm | Upsert de la config de finca (una fila; campos `null` = heredar default). |
| PUT | `/alert-configs/plot/{plot_id}` | farm | Upsert del override de lote. |
| GET | `/alert-configs/resolved/plot/{plot_id}` | farm | Config **efectiva** del lote (lote → finca → default), con el origen de cada valor: `{"max_drying_days": {"value": 12, "source": "farm"}}`. |
| DELETE | `/alert-configs/plot/{plot_id}` | farm | Elimina el override (vuelve a heredar). |

### 3.4 `crop-cycles`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/crop-cycles/create` | farm | Abre ciclo en un lote `active` sin ciclo activo (409 si ya hay). `cycle_number` lo asigna el service. |
| GET | `/crop-cycles/get` | farm | Filtros: `plot_id`, `status`. |
| GET | `/crop-cycles/get/{id}` | farm | Detalle + resumen de labores y cosechas del ciclo. |
| PUT | `/crop-cycles/update/{id}` | farm | Fechas/observaciones. |
| POST | `/crop-cycles/{id}/close` | farm | Cierra el ciclo (exige cosechas cerradas; asigna `end_date`). |
| DELETE | `/crop-cycles/delete/{id}` | farm | Solo sin registros colgados (RESTRICT). |

### 3.5 Labores del ciclo

Mismo patrón CRUD para las siete: `fertilizations`, `phytosanitary-apps`,
`irrigations`, `pest-monitorings`, `cultural-practices`, `flowering-records`,
`soil-analyses`:

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/<labor>/create` | farm | El body lleva `crop_cycle_id` (`plot_id` en `soil-analyses`). Valida enum `other` → exige `other_detail`. |
| POST | `/<labor>/bulk-create` | farm | Solo `fertilizations`, `phytosanitary-apps`, `irrigations`, `cultural-practices` y `flowering-records` (no las mediciones propias de cada lote). Body: campos comunes de la labor + `items: [{crop_cycle_id, quantity?, cost?}]`. El frontend precarga el reparto proporcional al área de cada lote (partes iguales si falta el área) y el usuario lo edita antes de guardar. Todos los ciclos deben estar activos y ser de la misma finca. Crea un registro por ciclo en una sola transacción (todo o nada). |
| GET | `/<labor>/get` | farm | Filtros: `crop_cycle_id` / `plot_id`, rango de fechas. |
| PUT | `/<labor>/update/{id}` | farm | |
| DELETE | `/<labor>/delete/{id}` | farm | Libre (las labores no tienen descendencia). |

`climate-records` igual, con `farm_id` obligatorio y `plot_id` opcional en el
body.

### 3.6 `supplies` (catálogo global)

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/supplies/create` | farm | Creación al vuelo desde formularios (D7). Única por `(name, supply_type)` → 409 si existe. |
| GET | `/supplies/get` | farm | Filtros: `supply_type`, `search`, `active`. |
| PUT | `/supplies/update/{id}` | farm | |
| POST | `/supplies/{id}/deactivate` | admin | Oculta sin borrar (histórico lo referencia). |
| DELETE | `/supplies/delete/{id}` | admin | Solo si ninguna labor lo referencia (RESTRICT). |

### 3.7 `employees` y `day-labors`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/employees/create` | farm | `farm_id` en body. |
| GET | `/employees/get` | farm | Filtros: `farm_id`, `active`, `search`. |
| PUT | `/employees/update/{id}` | farm | |
| POST | `/employees/{id}/deactivate` | farm | Preferido sobre delete (histórico de pagos). |
| DELETE | `/employees/delete/{id}` | farm | Solo sin registros (RESTRICT). |
| POST | `/day-labors/create` | farm | Jornal: `employee_id`, `activity_type` (+`other_detail`), `plot_id` opcional, `daily_value`. |
| GET | `/day-labors/get` | farm | Filtros: `employee_id`, `plot_id`, `paid`, rango de fechas. |
| PUT | `/day-labors/update/{id}` | farm | |
| POST | `/day-labors/{id}/pay` | farm | Marca `paid=true`, `paid_at=hoy`. |
| DELETE | `/day-labors/delete/{id}` | farm | |

### 3.8 `harvests` (sesión, patrón feria) y `harvest-works`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/harvests/create` | farm | Abre sesión: `crop_cycle_id`, `start_date`, tarifas default opcionales (`rate_per_kg` y/o `rate_per_day`). `pass_number` lo asigna el service. |
| GET | `/harvests/get` | farm | Filtros: `crop_cycle_id`, `status`. |
| GET | `/harvests/get/{id}` | farm | Detalle + trabajos diarios + total acumulado + calidad cereza si existe. |
| PUT | `/harvests/update/{id}` | farm | |
| POST | `/harvests/{id}/close` | farm | Cierra la sesión: recibe `total_cherry_kg` (precargado con la Σ de los trabajos que registraron kg; editable para incluir recolección familiar no paga o jornales sin pesaje). |
| DELETE | `/harvests/delete/{id}` | farm | Solo sin aportes a beneficios (RESTRICT). |
| POST | `/harvests/{id}/works/create` | farm | Registro diario: `employee_id`, `work_date`, `payment_type` (`per_kg` default / `per_day`). Si `per_kg`: `kg_collected` + `rate_per_kg` (default: el de la sesión). Si `per_day`: `day_value` (default: `rate_per_day` de la sesión) + `kg_collected` opcional. `total_value` lo calcula el service (kg × tarifa, o el jornal). |
| GET | `/harvests/{id}/works/get` | farm | Filtros: `employee_id`, `paid`, fecha. |
| PUT | `/harvests/works/update/{work_id}` | farm | Solo con cosecha `open`. |
| POST | `/harvests/works/pay` | farm | Pago masivo: body `{"work_ids": [...]}` → marca `paid`. |
| DELETE | `/harvests/works/delete/{work_id}` | farm | Solo con cosecha `open`. |

### 3.9 `quality-evals`

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/quality-evals/create` | farm | `stage` + (`harvest_id` xor `drying_id`) — el service valida coherencia (CHECK del modelo) y los campos de la etapa. |
| GET | `/quality-evals/get` | farm | Filtros: `stage`, `harvest_id`, `drying_id`, rango de fechas. |
| PUT | `/quality-evals/update/{id}` | farm | |
| DELETE | `/quality-evals/delete/{id}` | farm | |

### 3.10 `wet-processings` (beneficio)

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/wet-processings/create` | farm | Crea el beneficio con sus aportes: `farm_id` + `inputs: [{harvest_id, cherry_kg}]` (todas las cosechas de la misma finca; balance de masas validado → 409). |
| GET | `/wet-processings/get` | farm | Filtros: `farm_id`, `status`. |
| GET | `/wet-processings/get/{id}` | farm | Detalle + aportes + kg entrada (Σ pivote) + horas de fermentación calculadas. |
| PUT | `/wet-processings/update/{id}` | farm | Registra las etapas a medida que ocurren (flotes, despulpado, fermentación, lavado). Solo `in_progress`. |
| PUT | `/wet-processings/{id}/inputs` | farm | Reemplaza los aportes (solo `in_progress`, re-valida balance). |
| POST | `/wet-processings/{id}/complete` | farm | Exige `washed_kg`; congela el registro. |
| DELETE | `/wet-processings/delete/{id}` | farm | Solo sin aportes a secados (RESTRICT). |

### 3.11 `dryings` (secado, almacenamiento y salida a inventario)

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/dryings/create` | farm | `farm_id`, `method` (+`other_detail`), `start_date` + `inputs: [{wet_processing_id, wet_kg}]` (beneficios `completed`; balance vs `washed_kg` → 409). |
| GET | `/dryings/get` | farm | Filtros: `farm_id`, `status`, `destination`. |
| GET | `/dryings/get/{id}` | farm | Detalle + aportes + composición trazada (% por lote) + rendimiento calculado (F2). |
| PUT | `/dryings/update/{id}` | farm | Solo `in_progress`. |
| POST | `/dryings/{id}/humidity-checks/create` | farm | Medición intermedia: `check_date`, `humidity_pct`. |
| POST | `/dryings/{id}/complete` | farm | **Cierre** — ver contrato §4. Exige `final_humidity_pct`, `output_kg`, `destination` y datos de empaque. Si `destination=inventory`, crea `Inventory` + `Parchment` en la misma transacción. |
| POST | `/dryings/{id}/to-inventory` | farm | Para secados cerrados con `destination=stored`: los envía a inventario después (mismo contrato de precios). |
| DELETE | `/dryings/delete/{id}` | farm | Solo `in_progress` sin parchment (RESTRICT). |

### 3.12 Cuentas de caficultor (E2/E3)

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/farmer-accounts/create` | admin | Da acceso a un farmer: `{farmer_id, username, password}` → crea `User(role='farmer', person_id=farmer.person_id)`. 409 si esa persona ya tiene usuario. |
| POST | `/farmer-accounts/create-full` | admin | Farmer nuevo + cuenta en una operación: datos de `Person` + `Farmer` + credenciales. |

### 3.13 Dashboard y alertas

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `/dashboard/summary` | farm | KPIs con scoping: fincas/lotes activos, área por variedad, kg cereza y pergamino del periodo (`?from=&to=`), rendimientos, café en proceso. |
| GET | `/dashboard/alerts` | farm | Alertas y recordatorios activos calculados al momento (no se persisten): tipo, lote/finca, severidad, mensaje, valor vs umbral. |
| GET | `/dashboard/production` | farm | Series por periodo para gráficas (kg por mes, por finca/lote/variedad). |
| GET | `/dashboard/quality` | farm | Distribución de puntajes/defectos por finca/lote/variedad. |
| GET | `/dashboard/periods` | farm | Temporadas de cosecha del scope (`farm_id` / `plot_id` opcionales), de la más reciente a la más antigua, con `from`/`to`/`harvests`/`cherry_kg`. Alimenta los botones rápidos "última(s) N cosecha(s)" del selector de periodo (ver dashboards-alertas §2.1). |

> El detalle de widgets y queries se especifica en el doc 5 (dashboards y
> alertas). Aquí solo se fijan contratos y permisos.

### 3.14 Machine Learning

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| GET | `/plots/{id}/quality-projection` | farm | Proyección de calidad del ciclo activo del lote: features actuales → `{score, defects_pct, yield_factor, humidity_pct}` + metadatos (versión del modelo, completitud de datos). 409 si el lote no tiene ciclo activo. |

## 4. Contratos clave (ejemplos)

### Cierre de secado con destino inventario — `POST /dryings/{id}/complete`

Request:

```json
{
  "end_date": "2026-08-05",
  "final_humidity_pct": 11.2,
  "output_kg": 96.500,
  "packaging": "bolsa GrainPro + costal de fique",
  "sack_count": 2,
  "packed_at": "2026-08-06",
  "storage_place": "bodega finca",
  "destination": "inventory",
  "inventory_data": {
    "product_id": 1,
    "full_price": 3200000,
    "purchase_date": "2026-08-06"
  }
}
```

Comportamiento (transacción única, regla §6.4 del modelo):
1. Valida estado `in_progress`, humedad y kg presentes. Humedad fuera de
   10–12 % **no bloquea** — genera alerta (§7.2 arquitectura).
2. Marca el secado `completed`.
3. Si `destination = inventory`: crea `Inventory` + `Parchment` con
   `drying_id`, `farmer_id` = farmer de la finca, `variety` del lote
   dominante en la composición, `humidity` = final, `full_price` asignado por
   el productor y `purchase_price` calculado por el servicio existente (C1).
   `inventory_data` es obligatorio solo en este caso.

Response:

```json
{
  "id": 14,
  "status": "completed",
  "output_kg": 96.500,
  "yield_pct": 18.9,
  "traceability": [
    {"plot_id": 3, "plot_name": "La Loma", "share_pct": 62.1},
    {"plot_id": 5, "plot_name": "El Mirador", "share_pct": 37.9}
  ],
  "parchment_id": 88
}
```

### Config de alertas resuelta — `GET /alert-configs/resolved/plot/{id}`

```json
{
  "plot_id": 3,
  "values": {
    "fertilization_reminder_days": {"value": 90, "source": "farm"},
    "max_drying_days":             {"value": 15, "source": "plot"},
    "broca_alert_pct":             {"value": 2.0, "source": "default"}
  }
}
```

### Alerta del dashboard — elemento de `GET /dashboard/alerts`

```json
{
  "type": "broca_above_threshold",
  "severity": "high",
  "farm_id": 1,
  "plot_id": 3,
  "message": "Broca en 3.5 % (umbral 2 %) — último muestreo 2026-07-28",
  "value": 3.5,
  "threshold": 2.0
}
```

## 5. Estructura del módulo y capa de routers

La API es **solo una capa** del módulo (arquitectura §10). Estructura completa:

```
app/farm_operations/
    docs/                    # esta documentación
    models/                  # SQLAlchemy — misma Base y cadena de Alembic
        farm.py  plot.py  crop_cycle.py  harvest.py  supply.py
        wet_processing.py  drying.py  quality_eval.py  employee.py  ...
    services/                # lógica de dominio TRANSVERSAL (cruza recursos):
        traceability.py      #   recorrer la cadena completa de un secado/parchment
        mass_balance.py      #   validaciones de kg entre etapas
        inventory_bridge.py  #   cierre de secado → Inventory + Parchment (transacción)
        alerts.py            #   cálculo de alertas (config resuelta + datos)
    api/
        v1/                  # capa HTTP
            dependencies.py  #   require_farm_role, get_accessible_farm
            router.py        #   farm_router: compone todos los sub-routers
            farms/  plots/  alert_configs/  crop_cycles/
            fertilizations/  phytosanitary_apps/  irrigations/
            pest_monitorings/  cultural_practices/  flowering_records/
            soil_analyses/  climate_records/  supplies/  employees/
            day_labors/  harvests/  quality_evals/  wet_processings/
            dryings/  farmer_accounts/  dashboard/  ml/
    ml/                      # features.py, predictor.py, artifacts/
```

Reparto de responsabilidades:

| Capa | Contenido |
|---|---|
| `models/` | Solo definición ORM. Nunca lógica de negocio. |
| `api/v1/<recurso>/` | `router.py` + `schema.py` (contratos Pydantic) + `service.py` del recurso — **patrón existente** (`farmers/`). El service de recurso maneja su CRUD y validaciones locales. |
| `services/` | Operaciones que cruzan recursos o módulos: el cierre de secado que crea el `Parchment`, el balance de masas entre etapas, la trazabilidad completa, el cálculo de alertas. Los services de la API los invocan; nunca al revés. |

`router.py` raíz incluye cada sub-router con su prefijo y tag
(`farm-plots`, `farm-harvests`… para agrupar en Swagger).

## 6. Decisiones de este documento — para tu revisión

| # | Decisión | Racional / alternativa |
|---|---|---|
| A1 | Rol `user` (personal Shaya) **sin acceso** al módulo farm en v1 | E1 solo define farmer y admin. Si el personal necesita consultar cultivo, se agrega luego una vista read-only. |
| A2 | 404 (no 403) cuando un farmer pide un recurso de otra finca | No revelar que el recurso existe. Patrón estándar multi-tenant. |
| A3 | Los aportes (pivotes) se manejan **dentro** del recurso padre (`inputs` en create/update del beneficio y secado), no como CRUD independiente | Un aporte no tiene vida propia; editarlos sueltos permitiría romper el balance de masas con estados intermedios. |
| A4 | Las alertas se **calculan al consultar**, no se persisten en tabla | Sin estado que sincronizar ni jobs; con los volúmenes del sistema la query es barata. Si algún día se quiere "marcar como vista", se agrega tabla en ese momento. |
| A5 | `pass_number` y `cycle_number` los asigna el service (no vienen en el body) | Evita huecos y duplicados; el cliente no controla consecutivos. |
| A6 | Pago masivo de recolección (`/harvests/works/pay` con lista de ids) | El caso real es "pagarle la semana a Pedro": marcar uno por uno sería tedioso. |
| A7 | `to-inventory` como operación separada para secados `stored` | El café guardado en finca entra a inventario cuando el productor decida, con el mismo contrato de precios (R8). |
