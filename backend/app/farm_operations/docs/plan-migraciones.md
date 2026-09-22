# Farm Operations — Plan de Migraciones

> Documento 6 de la hoja de ruta ([arquitectura.md](arquitectura.md) §12).
> Materializa el [modelo de datos](modelo-datos.md) aprobado en Alembic.
> Estado: **✅ aprobado** (2026-09-16) — no se ha escrito código.
> Última actualización: 2026-09-16

---

## 1. Punto de partida

| Aspecto | Estado actual |
|---|---|
| Cadena de Alembic | Una sola, lineal. Head: `d4a7c9e12f56`. Las 26 migraciones históricas no construían la base desde cero (la raíz modificaba tablas que ninguna migración creaba); se **consolidan en una migración base** con el mismo ID `d4a7c9e12f56` y `down_revision = None`, que crea el esquema completo tal como está en producción. Las originales se archivan en `alembic/versions_archive/` (plan de implementación, 2.3). |
| Registro de modelos | Registro central `app/models_registry.py`, usado por la app, `alembic/env.py`, los scripts y las pruebas (plan de implementación, 2.5). Un modelo no registrado es invisible para `autogenerate` y rompe el flush de las tablas con FK hacia él. |
| Estilo de migración | Escritas a mano, docstring en español explicando el *porqué*, `revision`/`down_revision` hex, `upgrade()` y `downgrade()` completos. |
| Enums | `sa.Enum(..., name='fairstatusenum')` — nombre explícito, minúsculas, igual al nombre de la clase Python. |
| Ejecución | `docker-compose.yml` corre `alembic upgrade head` antes de levantar la API; en local se corre a mano. |

El módulo entra a **esta misma cadena** (decisión A1): ninguna cadena
paralela, ningún `branch_labels`.

## 2. Prerrequisitos de código (antes de la primera migración)

1. **Modelos** en `app/farm_operations/models/` (un archivo por tabla o por
   grupo afín), todos sobre `app.core.db.base.Base`.
2. **Registro**: `app/farm_operations/models/__init__.py` importa todos los
   modelos de cultivo, y el registro central `app/models_registry.py` importa
   ese paquete junto con los modelos del núcleo. La app, `env.py`, los scripts
   y las pruebas importan el registro, no listas propias.
3. **Relaciones solo desde el lado de cultivo**: `Farm.farmer` y
   `Drying.parchment` se declaran en los modelos de cultivo, sin
   `back_populates` en `Farmer` ni en `Parchment`. El núcleo solo gana la
   columna `parchments.drying_id` (M5): el inventario no conoce el módulo de
   cultivo.
4. **Enums Python** en `app/farm_operations/models/enums.py`, con el `name=`
   de Postgres fijado en cada `mapped_column(Enum(..., name=...))` para que
   modelo y migración coincidan.

## 3. Convenciones para estas migraciones

| Tema | Regla |
|---|---|
| Una migración por bloque funcional | 6 revisiones (§4). Cada una deja la base de datos en un estado coherente y desplegable por sí sola. |
| Nombres de enum en Postgres | Minúsculas, igual a la clase, **con prefijo `farm`** cuando el nombre sería genérico: `farmplotstatusenum`, `farmseverityenum`, `farmintensityenum`. Evita colisiones futuras con otros módulos (`severityenum` a secas es demasiado ambiguo). |
| Enums en downgrade | Toda migración que crea un tipo enum lo elimina en `downgrade()` (`sa.Enum(name=...).drop(op.get_bind())`). Postgres no lo borra solo al borrar la tabla. |
| Índices parciales | `op.create_index(..., postgresql_where=sa.text("status = 'active'"))`. |
| CHECKs | `sa.CheckConstraint(..., name='ck_<tabla>_<regla>')` con nombre explícito, para poder eliminarlos por nombre. |
| Timestamps | `created_at` con `server_default=sa.func.now()`, `DateTime(timezone=True)`. |
| `ondelete` | Exactamente como en el modelo de datos §6: `RESTRICT` en la cadena de trazabilidad, `CASCADE` solo en detalles y pivotes desde su cabecera. |
| Docstring | Español, explica el porqué y enlaza el documento (`modelo-datos.md §3.x`). |

## 4. Secuencia de migraciones

Cada revisión `Revises` la anterior; la primera revisa `d4a7c9e12f56`.

### M1 — `farm base: supplies, farms, plots, events, alert configs, employees`

Crea (modelo-datos §3.1–3.4, 3.7, 3.9): `supplies`, `farms`, `plots`,
`plot_events`, `alert_configs`, `employees`.

- Enums: `farmplotstatusenum`, `farmploteventtypeenum`, `farmsupplytypeenum`.
- FK `plots.renewed_from_plot_id → plots.id` (auto-referencia, RESTRICT).
- CHECKs: `ck_plots_planting_or_age`, `ck_plots_closed_has_date`,
  `ck_alert_configs_one_level` (`(farm_id IS NULL) != (plot_id IS NULL)`).
- Índice parcial único `uq_plots_farm_name_active` sobre `(farm_id, name)`
  `WHERE status = 'active'`.
- Únicos: `farms (farmer_id, name)`, `supplies (name, supply_type)`,
  `alert_configs.farm_id`, `alert_configs.plot_id`.

### M2 — `farm cycles and cycle records`

Crea (§3.5, 3.6, 3.8): `crop_cycles`, `climate_records`, `fertilizations`,
`phytosanitary_apps`, `irrigations`, `pest_monitorings`,
`cultural_practices`, `flowering_records`, `soil_analyses`.

- Enums: `farmcyclestatusenum`, `farmfertilizationmethodenum`,
  `farmseverityenum`, `farmintensityenum`, `farmculturalpracticetypeenum`.
- Índice parcial único `uq_crop_cycles_one_active` sobre `(plot_id)`
  `WHERE status = 'active'`; único `(plot_id, cycle_number)`.
- CHECK `ck_crop_cycles_dates` (`end_date IS NULL OR end_date >= start_date`).
- Índices compuestos `(crop_cycle_id, <fecha>)` en cada tabla de labores;
  `(farm_id, record_date)` en clima; `(plot_id, analysis_date)` en suelo.

### M3 — `farm harvests, harvest works, day labors`

Crea (§3.10–3.12): `harvests`, `harvest_works`, `day_labors`.

- Enums: `farmharveststatusenum`, `farmharvestpaymenttypeenum`,
  `farmlaboractivityenum`.
- Único `harvests (crop_cycle_id, pass_number)`.
- CHECK `ck_harvest_works_payment` (per_kg exige kg + tarifa; per_day exige
  `day_value`).
- `harvest_works.harvest_id` con `ondelete=CASCADE` (detalle de sesión);
  `employee_id` RESTRICT.

### M4 — `farm wet processing, drying, quality evals`

Crea (§3.13–3.17): `wet_processings`, `wet_processing_inputs`, `dryings`,
`drying_inputs`, `drying_humidity_checks`, `quality_evals`.

- Enums: `farmwetprocessingstatusenum`, `farmfermentationmethodenum`,
  `farmdryingstatusenum`, `farmdryingmethodenum`,
  `farmdryingdestinationenum`, `farmqualitystageenum`.
- Pivotes con `CHECK > 0` en kg y únicos `(cabecera, origen)`; `ondelete`
  CASCADE desde la cabecera, RESTRICT hacia el origen.
- CHECK `ck_quality_evals_stage_ref` (etapa ↔ FK coherentes) y rangos 0–100.
- CHECK `ck_wet_processings_fermentation` (`fermentation_end` exige
  `fermentation_start`).

### M5 — `link parchments to dryings`

Cambio a tabla existente (§4 del modelo de datos):

```python
op.add_column('parchments', sa.Column('drying_id', sa.Integer(), nullable=True))
op.create_foreign_key('fk_parchments_drying', 'parchments', 'dryings',
                      ['drying_id'], ['id'], ondelete='RESTRICT')
op.create_unique_constraint('uq_parchments_drying', 'parchments', ['drying_id'])
op.create_index('idx_parchment_drying_id', 'parchments', ['drying_id'])
```

`origin_batch` **no se toca** (R4). Los registros existentes quedan con
`drying_id = NULL` = café comprado. Downgrade: drop index, constraint, FK y
columna, en ese orden.

### M6 — `seed Shaya farmer`

Migración **de datos**, idempotente (decisión C4: la producción propia entra a
inventario con el farmer Shaya):

- Si no existe una `Person` con `document = 'SHAYA'` (marcador estable, no
  un nombre que pueda editarse): inserta `Person(full_name='Shaya',
  document='SHAYA')` y `Farmer(person_id, farm_name='Shaya',
  village='-', municipality='-')`.
- Si existe, no hace nada (permite correr la migración en una base que ya lo
  tenga por otra vía).
- Downgrade: elimina el farmer y la persona **solo si** ninguna `farm` ni
  `parchment` los referencia; si sí, aborta con mensaje claro.

**Orden:** M6 no depende de las tablas nuevas (inserta en `persons` y
`farmers`, que ya existen) y es requisito para registrar la finca propia desde
el principio, así que se ejecuta en el bloque 1B y en la cadena queda
inmediatamente después de M1 (plan de implementación, bloque 1B).

El rol `farmer` en `users.role` **no requiere migración** (columna `String`,
E3). Un catálogo inicial de `supplies` comunes (Urea, DAP, 25-4-24, cal
dolomita…) queda como **script opcional** `scripts/seed_supplies.py`, no como
migración: es conveniencia, no requisito para que la app funcione.

## 5. Procedimiento por migración

1. Escribir/ajustar los modelos y registrarlos (§2).
2. `alembic revision --autogenerate -m "<mensaje>"` **solo como borrador**:
   revisar el archivo generado línea por línea, completar lo que
   autogenerate no produce bien (índices parciales, CHECKs con nombre,
   `postgresql_where`, drop de enums en downgrade) y reescribir el docstring.
3. Local: `alembic upgrade head` → verificar con `\d <tabla>` en `psql` que
   constraints, índices y enums existen con los nombres esperados.
4. **Probar el downgrade**: `alembic downgrade -1` y de nuevo `upgrade head`.
   Una migración sin downgrade probado no se mezcla.
5. Correr la suite de tests del backend (los modelos nuevos no deben romper
   los existentes; M5 exige que `parchments` siga creándose sin `drying_id`).
6. Commit por migración (o por par M1+M2 si se hacen seguidas), mensaje
   `feat: farm operations migration <n> — <bloque>`.

## 6. Interacciones con otros documentos

| Con | Qué hay que tener en cuenta |
|---|---|
| Generador sintético (`--wipe`) | Con `RESTRICT` en toda la cadena, el borrado de datos sintéticos debe ir **en orden inverso de dependencia**: quality_evals → drying_inputs → dryings → wet_processing_inputs → wet_processings → harvest_works → harvests → labores → crop_cycles → plot_events → alert_configs → plots → employees → farms. El generador lo encapsula en una función `wipe_synthetic()`; nunca `TRUNCATE CASCADE`. |
| Servicio de inventario | Al cerrar un secado con destino inventario, `inventory_bridge.py` llama al servicio existente de creación de `Parchment` pasando `drying_id`; el schema Pydantic `ParchmentCreate` actual gana ese campo opcional. Es cambio de código, no de migración. |
| Alertas (`DEFAULTS`) | No viven en la base de datos; `alert_configs` solo guarda overrides. Ninguna migración de defaults. |

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| `autogenerate` no detecta bien enums existentes y propone recrearlos | Revisión manual obligatoria (§5.2); nunca aplicar un autogenerate sin leerlo. |
| Nombre de enum en el modelo ≠ nombre en la migración → la app falla al insertar | `name=` fijado en `enums.py` y copiado literal a la migración; el test de humo de M1 inserta un registro por enum. |
| Un modelo nuevo no importado en `env.py` → autogenerate lo omite en silencio | `models/__init__.py` importa todos y `env.py` importa el paquete; revisión de que la migración crea las 23 tablas del modelo de datos. |
| M5 sobre una base con datos reales de `parchments` | Es solo `ADD COLUMN NULL`: no bloquea, no reescribe filas. Sin riesgo de downtime a esta escala. |
| Migración de datos (M6) corriendo en entornos donde Shaya ya existe con otro documento | Idempotencia por `document = 'SHAYA'`; si hay un farmer "Shaya" sin ese documento, se **documenta** el paso manual de asignárselo antes de migrar, en vez de adivinar por nombre. |
