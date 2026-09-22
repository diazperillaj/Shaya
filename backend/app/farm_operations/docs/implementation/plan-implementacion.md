# Farm Operations — Plan de Implementación

> Primer documento de la fase de implementación. Convierte los seis documentos
> de planeación aprobados ([arquitectura.md](../arquitectura.md) §12) en
> bloques de trabajo ejecutables.
> Estado: **✅ aprobado** (2026-09-22).
> Última actualización: 2026-09-22

---

## 1. Enfoque

El módulo se construye en **bloques verticales**: cada bloque incluye
modelos, migración, servicios, API, pantallas y pruebas de una parte del
dominio, y termina con algo usable en la app. Frente a construir todo el
backend primero y el frontend después:

- los problemas de integración (contratos, permisos, uso desde el celular)
  aparecen en el primer bloque y no al final;
- cada bloque es desplegable por sí solo — las migraciones son aditivas y
  dejan la base en un estado coherente ([plan-migraciones.md](../plan-migraciones.md) §3);
- el orden sigue las dependencias de datos: no hay cosecha sin ciclo, ni
  secado sin beneficio.

| # | Bloque | Queda funcionando | Migraciones | Complejidad |
|---|---|---|---|---|
| 1A | Cimientos | App lista para usuarios externos, base reproducible, pruebas | Migración base consolidada | Alta — seguridad y patrones |
| 1B | Dominio base | Fincas, lotes, insumos, empleados, config. de alertas, cuentas farmer | M1, M6 | Media |
| 2 | Ciclos y labores | Seguimiento agronómico completo | M2 | Media — volumen de formularios |
| 3 | Cosechas y jornales | Recolección y pagos | M3 | Media |
| 4 | Beneficio, secado y calidad | Trazabilidad completa venta → lote | M4, M5 | Alta — pivotes, balance, transacción con inventario |
| 5 | Generador sintético | Sistema poblado y reproducible | — | Alta — metodología |
| 6 | Dashboard y alertas | Panel con periodos, KPIs y alertas | — | Media |
| 7 | Proyección de calidad | ML servido en la UI | — | Alta |

## 2. Hallazgos del código actual que condicionan el plan

Revisión del código existente (2026-09-22). Son situaciones que los
documentos de planeación no contemplaban; el plan las resuelve en el bloque
indicado.

### 2.1 El rol `farmer` expondría los módulos de Shaya — seguridad (1A)

Cerca de 65 endpoints existentes solo exigen sesión iniciada
(`get_current_user`); unos 40 exigen admin. Hoy basta, porque todo usuario
autenticado es personal de Shaya. Con cuentas para caficultores externos,
**un farmer podría leer ventas, clientes, gastos, inventario y caficultores**
por la API, y consultar todo el negocio a través del asistente: el chatbot
valida la misma cookie y solo distingue admin.

La especificación de API (§2) cubría la dirección contraria (el rol `user`
sin acceso al módulo de cultivo), no esta. Resolución — **condición previa a
crear cualquier cuenta farmer**:

- dependencia `require_staff` (lista explícita de roles de personal: todo lo
  demás se rechaza) aplicada a nivel de `include_router` en `api_v1.py` a
  todos los routers existentes salvo `auth` — un solo lugar, auditable. Si
  algún endpoint de cuenta propia (p. ej. cambiar la contraseña) debe quedar
  abierto al farmer, se declara como excepción explícita;
- el chatbot responde 403 al rol `farmer`;
- el menú del frontend se filtra por rol: el farmer solo ve "Cultivo";
- **test de auditoría de rutas**: recorre todas las rutas registradas y
  verifica que una sesión farmer recibe 403 en toda ruta fuera de `/farm` y
  `/auth` (salvo las excepciones declaradas). Un router nuevo sin guardia
  rompe el test.

### 2.2 `UserRole` solo admite `admin` y `user` (1A)

`UserResponse.role` usa ese enum y es el modelo de respuesta de
`GET /users/get`: el primer usuario `farmer` haría fallar la serialización y
la página de Usuarios dejaría de cargar. Además, crear un farmer por
`/users/create` generaría una `Person` nueva sin la faceta `Farmer`.
Resolución: `UserRole` incluye `farmer` para lectura; `/users/create` sigue
aceptando solo roles de personal; las cuentas farmer se crean únicamente por
`/farm/farmer-accounts/*`, que enlaza la `Person` existente (E3).

La columna `users.role` es nullable y sin restricción, así que antes de
definir la lista de roles de personal se consultaron los valores reales:
1 `admin` y 4 `user`, sin nulos ni valores inesperados (verificado
2026-09-22). No hace falta migración de normalización.

### 2.3 La cadena de migraciones no construye la base desde cero (1A)

La migración raíz (`8b54c737047e`) modifica una columna de `persons`: asume
que las tablas base (`persons`, `users`, `farmers`, `products`,
`inventories`, `parchments`…) ya existen, y ninguna migración las crea — se
crearon fuera de Alembic. Sobre una base vacía, `alembic upgrade head` falla
en la primera migración. Consecuencias:

- la base de pruebas no se puede construir con migraciones;
- `docker compose up` sobre un volumen vacío no levanta el backend (el
  arranque corre `alembic upgrade head`): **quien clone el repositorio no
  puede ejecutar el proyecto**, y no es posible montar un entorno de demo.

Resolución: consolidar las 26 migraciones en una **migración base** que crea
el esquema completo actual y **conserva el ID del head (`d4a7c9e12f56`)**
con `down_revision = None`.

- Producción no requiere ninguna acción: ya está en `d4a7c9e12f56`
  (verificado 2026-09-22, PostgreSQL 16.14).
- Las bases nuevas (pruebas, CI, demo) se construyen completas.
- El plan de migraciones sigue válido: M1 revisa `d4a7c9e12f56`.
- Las migraciones originales se archivan fuera de la ruta de Alembic; su
  historia queda en git.
- **Verificación obligatoria**: el esquema de una base construida desde la
  migración base debe ser idéntico al de producción (comparación de
  `pg_dump --schema-only`). Si difieren, manda producción.

### 2.4 Los errores de validación devuelven 500 (1A)

El manejador global de `RequestValidationError`
(`core/exceptions/handlers.py`) solo responde cuando el campo que falló está
en su diccionario de mensajes (cinco campos de usuarios y personas). Para
cualquier otro campo no devuelve respuesta y el cliente recibe **500**
(verificado con una prueba aislada). Afecta hoy a los módulos existentes y
afectaría a todo el módulo de cultivo, cuyo contrato es 422 con detalle
([especificacion-api.md](../especificacion-api.md) §1). Resolución: cuando
no haya mensaje personalizado, delegar en el manejador por defecto de
FastAPI.

### 2.5 No hay registro central de modelos (1A)

`alembic/env.py` y `scripts/import_excel.py` mantienen cada uno su propia
lista de imports de modelos. La nueva FK `parchments.drying_id → dryings.id`
hace que cualquier proceso que inserte un `Parchment` necesite los modelos
de cultivo cargados: si no, SQLAlchemy falla al hacer flush con
`NoReferencedTableError` (verificado). El script de importación de Excel se
rompería. Resolución: un módulo de composición (`app/models_registry.py`, al
nivel de `main.py`) que importa todos los modelos — núcleo y cultivo — y que
usan todos los puntos de entrada: `main.py`, `env.py`, scripts y pruebas.

Complemento de diseño: **las dependencias van en una sola dirección** — el
módulo de cultivo depende del núcleo, nunca al revés. Las relaciones se
declaran desde el lado de cultivo (`Farm.farmer`, `Drying.parchment`) sin
`back_populates` en `Farmer` ni en `Parchment`; el núcleo solo gana la
columna `parchments.drying_id`. El inventario no sabe que el módulo de
cultivo existe.

### 2.6 La navegación del frontend es por estado, sin URLs (1A)

La app tiene una sola ruta (`/`) y cambia de módulo con un estado
(`activeMenuItem` + `menuConfig.tsx`). Funciona para los módulos existentes,
que son planos (tabla + modales). El de cultivo es jerárquico (finca → lote
→ ciclo → labores; secado → trazabilidad) y el panel de alertas enlaza a
entidades concretas ([dashboards-alertas.md](../dashboards-alertas.md) §7).
Resolución: el módulo de cultivo usa **rutas con URL anidadas bajo
`/cultivo/...`** (react-router-dom ya está instalado), integradas con el menú
existente; el resto de la app no cambia. Da botón atrás, recarga sin perder
la posición y enlaces directos desde alertas.

### 2.7 No hay infraestructura de pruebas (1A)

`pytest` está en `requirements.txt`, pero no existen `backend/tests`,
`conftest.py` ni CI; la carpeta `chatbot/tests/golden` está vacía. Ver §4.

### 2.8 Los componentes de gráfica están embebidos (6)

`KpiCard`, `ChartCard`, `DonutChart`, `CustomTooltip` y `GlobalChartDefs`
son funciones privadas dentro de `DashboardPage.tsx`. Reutilizarlos exige
extraerlos primero a componentes compartidos.

### 2.9 Otros hechos que el plan asume

- **Migraciones automáticas al desplegar**: el arranque del backend corre
  `alembic upgrade head`; cada bloque fusionado migra producción en el
  siguiente despliegue.
- **Excepciones**: no hay excepciones de dominio — los servicios existentes
  lanzan `HTTPException`. Los servicios de cultivo usan excepciones de
  dominio (§5.2) para poder reutilizarse fuera de la API.
- **Chatbot**: los *default privileges* de `chatbot_ro` ya le dan lectura a
  las tablas nuevas; no requiere acción, salvo el bloqueo de 2.1.

## 3. Bloques

### Bloque 1A — Cimientos

**Objetivo:** la app queda lista para recibir el módulo y para tener usuarios
externos de forma segura, y el proyecto se puede levantar desde cero. No crea
tablas de cultivo; es valioso por sí solo. Puede ir en uno o dos PRs
(infraestructura / seguridad y navegación).

1. **Migración base consolidada** (2.3), con la verificación de esquema
   contra producción.
2. **Registro central de modelos** (2.5); `env.py`, `main.py` y scripts lo
   usan.
3. **Esqueleto del paquete** `app/farm_operations/` (`models/`,
   `services/`, `api/v1/`, `ml/`, `exceptions.py`) y `farm_router` montado
   en `api_v1.py` bajo `/farm`.
4. **Seguridad de roles** (2.1, 2.2): `require_staff`,
   `require_farm_role`, `UserRole` y bloqueo del farmer en el chatbot.
   (`get_accessible_farm` necesita el modelo `Farm`: va en el 1B.)
5. **Manejo de errores** (2.4) y base `DomainError` (§5.2).
6. **Infraestructura de pruebas** (§4), incluido el test de auditoría de
   rutas.
7. **Frontend**: rutas `/cultivo/*` integradas al menú; `MenuItem.roles`
   para filtrar el menú por rol; pantalla de aterrizaje del farmer
   (provisional hasta el bloque 6).

**Terminado cuando:**
- `docker compose up` sobre un volumen vacío levanta el backend con el
  esquema completo;
- con una sesión farmer, el test de auditoría pasa (403 en todo lo que no es
  `/farm` ni `/auth`) y el chatbot la rechaza;
- los módulos existentes funcionan igual para `admin` y `user`;
- un error de validación devuelve 422 con detalle.

### Bloque 1B — Dominio base (M1 + M6)

**Referencias:** [modelo-datos.md](../modelo-datos.md) §3.1–3.4, 3.7, 3.9 ·
[especificacion-api.md](../especificacion-api.md) §3.1–3.3, 3.6, 3.7
(empleados), 3.12 · [plan-migraciones.md](../plan-migraciones.md) M1, M6.

**Backend**
- Modelos y M1: `supplies`, `farms`, `plots`, `plot_events`,
  `alert_configs`, `employees`.
- **M6 (farmer Shaya) se adelanta a este bloque**: no depende de tablas
  nuevas (inserta en `persons` y `farmers`, que ya existen) y es requisito
  para registrar la finca propia desde el principio (C4). Antes de fijar el
  marcador `document = 'SHAYA'`, verificar que no choque con la validación
  numérica del documento en los formularios de personas (editar el farmer
  Shaya desde la UI no debe fallar).
- `get_accessible_farm` (scoping por finca), que depende del modelo `Farm`.
- Diccionario `DEFAULTS` de alertas (valores de dashboards-alertas §4): lo
  necesita ya el endpoint de configuración resuelta; el bloque 6 lo reutiliza.
- Endpoints de fincas, lotes (incluye `close`, `reopen`,
  `renewal-defaults` y eventos), configuración de alertas, insumos,
  empleados y cuentas farmer.

**Frontend** (`/cultivo`)
- Fincas: lista y formulario (el admin elige el farmer; el farmer solo
  registra las suyas).
- Detalle de finca con sus lotes; formulario de lote con siembra y
  procedencia de la semilla; eventos; cerrar y reabrir; "renovar lote" con el
  formulario precargado.
- Catálogo de insumos con creación al vuelo (reutilizable en los bloques
  siguientes), empleados, y configuración de alertas que muestra el origen de
  cada valor (lote, finca o default).
- Admin: dar cuenta a un farmer existente, o crear farmer y cuenta en una
  sola operación.

**Pruebas:** scoping (el farmer A recibe 404 sobre la finca de B); CHECK del
lote (fecha de siembra o edad); nombre de lote reutilizable tras el cierre
(índice parcial); resolución lote → finca → default; M6 idempotente.

**Terminado cuando:** el admin crea un farmer con cuenta; el farmer inicia
sesión, ve solo "Cultivo" y registra su finca, lotes, empleados e insumos; la
finca propia de Shaya queda registrada con el farmer Shaya.

### Bloque 2 — Ciclos y labores (M2)

**Referencias:** modelo-datos §3.5, 3.6, 3.8 · especificacion-api §3.4, 3.5 ·
plan-migraciones M2.

**Backend**
- Modelos y M2: `crop_cycles`, `climate_records` y las siete tablas de
  labores.
- Endpoints de ciclos (abrir y cerrar) y CRUD uniforme de labores y clima;
  validación compartida de `other_detail`.
- **Registro en varios lotes a la vez**: `POST /<labor>/bulk-create` crea un
  registro por ciclo en una sola transacción. El modelo sigue siendo un
  registro por ciclo — el ML necesita la labor atribuida a cada lote —, pero
  quien tiene 20 lotes no repite el formulario 20 veces. Cantidad y costo se
  reparten proporcionalmente al área de cada lote (en partes iguales si falta
  el área), editables antes de guardar. Aplica a las labores que se ejecutan
  igual en varios lotes (fertilización, fitosanitarios, riego, labores
  culturales, floración); no a las mediciones propias de cada lote (monitoreo
  de plagas, análisis de suelo).

**Frontend**
- En el detalle del lote: panel del ciclo activo (abrir y cerrar) e
  historial de labores por tipo.
- Formularios cortos pensados para el celular: fecha de hoy por defecto,
  insumo con búsqueda y creación al vuelo.
- Selector "aplicar a: este lote / varios lotes / toda la finca" en las
  labores que lo admiten; clima por finca con lote opcional.

**Pruebas:** un solo ciclo activo por lote (409); no se abre ciclo en un lote
cerrado; `other_detail` exigido; `bulk-create` todo o nada; reparto por área.

**Terminado cuando:** el farmer abre un ciclo, registra cualquier labor desde
el celular en menos de un minuto, y registra una fertilización de toda la
finca en una sola operación.

### Bloque 3 — Cosechas y jornales (M3)

**Referencias:** modelo-datos §3.10–3.12 · especificacion-api §3.7
(jornales), 3.8 · plan-migraciones M3.

**Backend**
- Modelos y M3: `harvests`, `harvest_works`, `day_labors`.
- Endpoints de cosecha (abrir; cerrar con el total precargado), trabajos
  diarios al peso o por jornal, pago masivo, jornales y su pago.

**Frontend**
- Sesión de cosecha estilo feria: abrir, registrar la recolección diaria por
  empleado con las tarifas por defecto de la sesión, acumulado en vivo,
  cerrar.
- Pagos: trabajos y jornales pendientes por empleado; pago masivo por
  selección.

**Nota:** la composición de la cosecha (% maduros, verdes, brocados) se
guarda en `quality_evals`, que nace en M4 — el formulario de composición se
agrega a la pantalla de cosecha en el bloque 4.

**Pruebas:** CHECK de modalidad de pago; `total_value` calculado;
`pass_number` consecutivo; trabajos de una cosecha cerrada no editables;
total precargado = Σ kg registrados.

**Terminado cuando:** el farmer maneja una semana de cosecha real:
recolección mixta (al peso y por jornal), liquidación de pagos y cierre con
su total.

→ **Hito A** (§6).

### Bloque 4 — Beneficio, secado, calidad y puente a inventario (M4 + M5)

**Referencias:** modelo-datos §3.13–3.17, §4, §6 · especificacion-api
§3.9–3.11, §4 · plan-migraciones M4, M5, §6.

**Backend**
- Modelos y M4 (`wet_processings`, `dryings`, pivotes,
  `drying_humidity_checks`, `quality_evals`); M5 (`parchments.drying_id`).
- Servicios `mass_balance.py`, `traceability.py` e `inventory_bridge.py`.
- Endpoints de beneficio, secado (incluye `complete`, `to-inventory` y
  mediciones de humedad) y calidad.
- Inventario: `ParchmentCreate` y su servicio aceptan `drying_id` opcional;
  el puente reutiliza ese servicio y no duplica la regla de 3 de
  `purchase_price`.

**Frontend**
- Beneficio: elegir cosechas con los kg aportados; registrar las etapas a
  medida que ocurren (flotes, despulpado, fermentación, lavado).
- Secado: elegir beneficios, mediciones de humedad, cierre con destino y
  datos de inventario (producto, `full_price`, fecha).
- Composición en cereza dentro de la pantalla de cosecha; calidad en
  pergamino en el secado.
- **Vista de trazabilidad**: desde un secado, composición por lote → ciclos →
  labores. En el inventario existente, el pergamino producido muestra su
  origen con enlace a esa vista.

**Pruebas** — el bloque que más las necesita: exceder el total de una
cosecha → 409 sin cambios en la base; reparto de una cosecha entre varios
beneficios; cierre de secado atómico (si falla la creación del `Parchment`,
el secado no queda cerrado); `purchase_price` con el `full_price` asignado;
composición porcentual de una mezcla; recorrido de trazabilidad en ambos
sentidos; CHECK de etapa de calidad.

**Terminado cuando:** un pergamino producido se rastrea desde su venta hasta
sus lotes, ciclos y labores, y todo error de balance o de cierre deja la base
intacta.

→ **Hito B** (§6).

### Bloque 5 — Generador de datos sintéticos

**Referencias:** [generador-sintetico-ml.md](../generador-sintetico-ml.md)
§2, §3, §8 · plan-migraciones §6.

- `scripts/farm_ml/rules.py` (`RULES_VERSION` y reglas con dirección,
  fuente, forma y parámetros) y `generate_synthetic.py` con sus parámetros,
  niveles de faltantes, semilla, validación automática y artefacto de
  auditoría.
- El generador escribe vía ORM pero **reutiliza los servicios de dominio**
  donde vive una regla (numeración de ciclos y pasadas, balance de masas,
  puente a inventario): los datos sintéticos pasan las mismas validaciones
  que los reales. Por eso los servicios no dependen de FastAPI (§5.2).
- `wipe_synthetic()` en orden inverso de dependencia.
- Dependencias de herramientas (`pandas`, `pyarrow`) en un
  `requirements-dev.txt`: no entran a la imagen de producción.

**Dónde corre:** en la base de **desarrollo**. Producción recibe solo el
artefacto entrenado (bloque 7) y no mezcla fincas ficticias con las reales.
Para una demo pública se levanta un entorno aparte poblado con el generador
(posible gracias a la migración base de 2.3).

**Pruebas:** una generación mínima (1 finca, 1 año) en la base de pruebas pasa
la validación; `--wipe` deja cero filas sintéticas y no toca las reales.

**Terminado cuando:** dos corridas con la misma semilla producen el mismo
dataset, la validación pasa, y las pantallas de los bloques 1–4 navegan las
fincas sintéticas con normalidad.

→ **Hito C** (§6).

### Bloque 6 — Dashboard y alertas

**Referencias:** [dashboards-alertas.md](../dashboards-alertas.md) completo ·
especificacion-api §3.13.

- **Primero**: extraer los componentes de gráfica de `DashboardPage.tsx` a
  `components/charts/` (2.8), sin cambio visual en el dashboard existente.
- `services/alerts.py` (registro `CHECKS`, `DEFAULTS` del bloque 1B) y
  agrupación de temporadas para `/periods`.
- Endpoints `summary`, `alerts`, `production`, `quality` y `periods`.
- Frontend: dashboard con selector de periodo (rango personalizado y botones
  rápidos, incluidos "última(s) N cosecha(s)"), KPIs, gráficas, panel de
  alertas con enlaces a las rutas `/cultivo/...` y widgets propios de cada
  rol. El dashboard pasa a ser la pantalla de aterrizaje del farmer.

**Pruebas:** cada tipo de alerta con un caso que la dispara y uno que no;
agrupación de temporadas (brecha de 45 días); los widgets de estado ignoran
el periodo.

**Rendimiento:** con el volumen sintético por defecto, cada endpoint del
dashboard responde en menos de 500 ms — por eso este bloque va después del
generador.

**Terminado cuando:** con datos sintéticos todos los widgets muestran datos
coherentes, los botones rápidos eligen las temporadas correctas, y cada tipo
de alerta aparece al menos una vez y enlaza a su entidad.

→ **Hito D** (§6).

### Bloque 7 — Proyección de calidad (ML)

**Referencias:** generador-sintetico-ml §4–§8.

1. `ml/features.py` **con sus pruebas primero** (fixture con valores
   calculados a mano, incluida una mezcla ponderada): son la garantía del
   resto.
2. `train.py`: validación agrupada por finca, baselines y artefacto
   versionado.
3. `evaluate.py`: reporte con métricas, chequeos direccionales y de forma, y
   curva de faltantes.
4. `predictor.py`, endpoint `quality-projection` y tarjeta de proyección en
   el dashboard (con `completeness` y descargo).
5. Test de humo del serving.

Dependencias de inferencia (`scikit-learn`, `joblib`) en `requirements.txt`;
las de entrenamiento y evaluación, en `requirements-dev.txt`.

**Terminado cuando:** el reporte de `evaluate.py` pasa todos los chequeos de
generador-sintetico-ml §7, y la proyección aparece en la UI con su
completitud, la versión del modelo y el descargo.

→ **Hito E** (§6).

## 4. Estrategia de pruebas

| Nivel | Qué cubre | Cómo |
|---|---|---|
| Unitario | Funciones puras: balance de masas, agrupación de temporadas, resolución de umbrales, reparto por área, agregaciones de features | pytest, sin base de datos |
| Integración | Endpoints, permisos y scoping, constraints (CHECK, índices parciales), transacciones y rollback | `TestClient` contra **Postgres real** |
| Migraciones | Cadena completa desde cero; `downgrade -1` + `upgrade` de cada migración nueva | Fixture de sesión |
| Manual | Flujos completos en la app | Con datos sintéticos, desde el bloque 5 |

Decisiones de la infraestructura:

- **Postgres real, no SQLite**: el modelo usa índices parciales, CHECKs con
  nombre y enums nativos, que SQLite no reproduce con fidelidad.
- **Todo en Docker y aislado**: `docker-compose.test.yml` (proyecto propio
  `shaya-test`) levanta un Postgres 16 efímero con los datos en memoria y un
  contenedor que corre pytest con el mismo Python que producción. Las pruebas
  nunca tocan la base de desarrollo ni la de producción.
- Esquema construido con `alembic upgrade head` — posible tras 2.3 — de modo
  que cada corrida valida también la cadena de migraciones.
- Aislamiento por prueba con transacción y rollback; fábricas simples para
  farmer, finca, lote y ciclo.
- Clientes autenticados por rol (`admin`, `user`, `farmer`) como fixtures.
- Opcional: workflow de GitHub Actions con un servicio de Postgres que corre
  la suite en cada PR.

## 5. Convenciones de implementación

### 5.1 Flujo de trabajo

- Una rama por bloque (`feat/farm-1a-foundations`, `feat/farm-1b-base`…) y
  un PR a `main` que enlaza los documentos de referencia y lleva el checklist
  de §5.3.
- Commits breves en inglés, formato convencional (`feat:`, `fix:`, `docs:`,
  `test:`, `refactor:`).
- **Los documentos de planeación son la fuente de verdad**: si durante la
  implementación algo se desvía del diseño, el documento se actualiza en el
  mismo PR.

### 5.2 Código

- Los servicios transversales (`farm_operations/services/`) **no dependen
  de FastAPI**: lanzan excepciones de dominio que heredan de una base
  `DomainError` (definida en `app/core/exceptions/`, con su código HTTP) y un
  único manejador global las traduce. Así los reutilizan la API, el
  generador y futuros scripts.
- Dirección de dependencias: cultivo → núcleo, nunca al revés (2.5).
- Enums de cultivo con prefijo `farm` en Postgres (plan-migraciones §3).

### 5.3 Definición de terminado (todo PR)

- [ ] Migración con `upgrade` y `downgrade` probados (si aplica).
- [ ] Pruebas nuevas y existentes en verde, incluida la auditoría de rutas.
- [ ] Pantallas probadas en escritorio y en celular.
- [ ] Documentación actualizada si hubo desviación del diseño.
- [ ] Tabla de seguimiento (§7) actualizada.

### 5.4 Despliegue

- Respaldo (`pg_dump`) antes de desplegar un bloque con migraciones: el
  arranque del backend las aplica solo.
- El módulo se despliega de forma incremental sin *feature flags*: las
  cuentas farmer solo las crea el admin, así que ningún usuario externo lo ve
  hasta que se decida abrirlo (hito D). La finca propia se usa desde el hito A.

## 6. Hitos

| Hito | Tras | Qué significa |
|---|---|---|
| A — Piloto con la finca propia | Bloque 3 | La operación de campo de Shaya (labores, cosechas, pagos) se registra en el sistema. Primera retroalimentación real antes de los bloques más complejos. |
| B — Trazabilidad completa | Bloque 4 | Una venta se rastrea hasta sus lotes: la promesa central del módulo. |
| C — Sistema poblado | Bloque 5 | Datos sintéticos reproducibles para desarrollo, demo y entrenamiento. |
| D — Apertura a caficultores | Bloque 6 | Se crean cuentas para farmers externos: ya tienen operación, trazabilidad, dashboard y alertas. |
| E — Proyección de calidad | Bloque 7 | El modelo entrenado sirve proyecciones en producción. |

## 7. Seguimiento

| Bloque | PR | Estado | Notas |
|---|---|---|---|
| 1A — Cimientos | — | ⬜ | |
| 1B — Dominio base | — | ⬜ | |
| 2 — Ciclos y labores | — | ⬜ | |
| 3 — Cosechas y jornales | — | ⬜ | |
| 4 — Beneficio, secado y calidad | — | ⬜ | |
| 5 — Generador sintético | — | ⬜ | |
| 6 — Dashboard y alertas | — | ⬜ | |
| 7 — Proyección de calidad | — | ⬜ | |

⬜ pendiente · 🟡 en curso · ✅ fusionado

## 8. Ajustes a los documentos de planeación

| Documento | Ajuste |
|---|---|
| especificacion-api.md §2 | Endpoints existentes restringidos a roles de personal; `UserRole` y creación de cuentas farmer (2.1, 2.2). |
| especificacion-api.md §3.5 | `bulk-create` de labores con reparto por área (bloque 2). |
| plan-migraciones.md §1, §2, §4 | Migración base consolidada con el ID del head (2.3); registro central de modelos y relaciones solo desde el lado de cultivo (2.5); M6 se adelanta al bloque 1B. |
| dashboards-alertas.md §7 | Enlaces de alertas a rutas `/cultivo/...` (2.6); extracción de componentes de gráfica (2.8). |

## 9. Fuera de alcance

- Herramientas de análisis de cultivo en el asistente: el chatbot ya puede
  leer las tablas; agregarle herramientas es una fase posterior.
- Migrar el resto de la app a rutas con URL: solo el módulo de cultivo las
  usa.
- App móvil nativa o captura offline ([arquitectura.md](../arquitectura.md) §2).
- Reentrenamiento programado y recarga del modelo en caliente
  (generador-sintetico-ml §10).
