# Farm Operations — Generador de Datos Sintéticos y Pipeline ML

> Documento 4 de la hoja de ruta ([arquitectura.md](arquitectura.md) §12).
> Basado en el modelo de datos y la API aprobados.
> Estado: **✅ aprobado** (2026-09-16) — revisión metodológica externa incorporada.
> Última actualización: 2026-09-16

---

## 1. Objetivo y marco metodológico

Predecir la calidad esperada del café (4 variables de `quality_evals` etapa
`parchment`: `score`, `defects_pct`, `yield_factor`, `humidity_pct`) a partir
de las variables registradas durante el ciclo del lote.

No hay datos reales. Por eso (arquitectura §9.3):

- Se construye un **generador de datos sintéticos** cuyas reglas provienen de
  literatura agronómica (Cenicafé, protocolo SCA).
- El modelo se entrena y evalúa sobre esos datos.
- **Alcance declarado**: el experimento evalúa la capacidad del pipeline
  (captura → features → entrenamiento → serving → UI) para **recuperar
  relaciones agronómicas previamente definidas en un entorno sintético
  controlado**. No demuestra que el modelo prediga la calidad de café real:
  un modelo entrenado sobre un generador solo puede recuperar las reglas del
  generador. Esto se declara explícitamente en la documentación y en la UI.
- Con datos reales futuros, el paso con verdadero peso empírico es la
  **evaluación externa**: el mismo pipeline reentrenado y evaluado contra
  mediciones reales, sin cambiar código.

## 2. Estrategia del generador: poblar la base de datos, no un CSV

El generador **no produce un CSV directo de features**. Produce **registros
completos en la base de datos** a través de los modelos ORM: fincas, lotes,
ciclos, labores, cosechas, beneficios, secados y evaluaciones de calidad,
coherentes entre sí (fechas encadenadas, balance de masas válido, estados
correctos).

Racional (decisión G1, ver §9):

1. El dataset de entrenamiento se construye con **el mismo módulo
   `features.py` que usará la inferencia en producción**, lo que garantiza
   **cero divergencia** entre entrenamiento y serving. Precisión importante:
   compartir el código **no** garantiza que la extracción sea correcta — un
   bug presente en ambos lados produce métricas excelentes y predicciones
   equivocadas. Por eso la corrección de `features.py` se verifica con
   **tests de consistencia independientes del modelo** (§7.5), no con las
   métricas.
2. Los datos sintéticos sirven además como **datos de demostración y prueba**
   de todo el módulo (dashboards con contenido, trazabilidad navegable,
   pruebas manuales de la app sin inventar datos a mano).

Los datos sintéticos se generan bajo un **`Farmer` sintético marcado**
(`observation = "SYNTHETIC_ML_DATA"`), de modo que:
- `--wipe` los borra completos sin tocar datos reales;
- las queries de dashboard/producción reales pueden excluirlos si conviven.

## 3. Diseño del generador

### 3.1 Escala por defecto (parámetros CLI)

| Parámetro | Default | Descripción |
|---|---|---|
| `--farms` | 12 | Fincas sintéticas (altitudes 1.200–2.000 m). |
| `--plots-per-farm` | 2–6 (aleatorio) | Lotes por finca, variedades mezcladas. |
| `--years` | 5 | Años simulados hacia atrás → 1–2 ciclos/año por lote. |
| `--seed` | 42 | Semilla global: **todo reproducible** (dataset idéntico con el mismo `seed` + `rules_version`). |
| `--missing-level` | `realistic` | Simulación de datos faltantes (ver §3.6). |
| `--wipe` | off | Borra lo sintético antes de generar. |

Resultado esperado: ≈ 600–1.500 secados cerrados (filas de entrenamiento).

### 3.2 Proceso generativo por lote-ciclo

Para cada ciclo se simula la secuencia real, en orden, con fechas coherentes
y respetando la jerarquía del modelo de datos (finca → lote → ciclo →
cosechas → beneficio → secado, con mezclas vía pivotes):

1. **Lote**: variedad (con perfil de taza y susceptibilidad a roya
   **independientes**, ver §3.3), altitud de la finca ± ruido local, edad del
   cultivo (avanza con los años; zocas ocasionales reinician la edad efectiva
   y generan `plot_events`), sombra, suelo, densidad.
2. **Clima del ciclo**: la temperatura se genera **acoplada a la altitud**
   (gradiente térmico ≈ −0,6 °C por cada 100 m) **más ruido local y
   estacional** — ni variables independientes ni relación determinista.
   Lluvia mensual con estacionalidad bimodal colombiana + ruido por finca/año
   (años Niño/Niña simulados).
3. **Labores**: cada finca sintética tiene un "nivel de manejo" latente
   (bueno / medio / descuidado) que determina frecuencia de fertilización,
   deshierbas, monitoreos y riegos. Ese nivel **no se guarda en la DB** — el
   modelo debe inferirlo de los registros, como pasaría en la realidad (sí se
   guarda en el artefacto de auditoría, §3.7).
4. **Sanidad**: broca y roya evolucionan según clima (broca sube con calor y
   cosechas dejadas; roya con lluvia prolongada **y según la susceptibilidad
   de la variedad** — interacción variedad × roya) y bajan con aplicaciones.
   La infestación de broca en campo (`pest_monitorings.broca_pct`) es un
   **indicador previo**: alimenta el `bored_pct` de la cereza en la cosecha
   (atenuado por las aplicaciones hechas entre el muestreo y la recolección),
   y es ese `bored_pct` el que entra a los mecanismos de calidad — no la
   infestación de campo directamente.
5. **Floración** → cosecha ≈ 32 semanas después (± 2), 1–3 pasadas.
6. **Cosecha**: % maduros depende del nivel de manejo y de la presión de la
   pasada; recolectores sintéticos con kg diarios; calidad `cherry` registrada.
7. **Beneficio**: flotes ∝ broca y % verdes; horas hasta despulpado y horas de
   fermentación muestreadas alrededor de las ventanas correctas (la ventana de
   fermentación **se desplaza con la temperatura ambiente**, §3.3), con colas
   (errores de manejo) más frecuentes en fincas descuidadas.
8. **Secado**: método según finca; los días de secado dependen simultáneamente
   de **método, temperatura y lluvia del periodo**; humedad final alrededor de
   10–12 con desvíos.
9. **Calidad `parchment`** (targets): calculada con los mecanismos de §3.3
   + ruido calibrado (§3.5).
10. **Mezclas**: ~25 % de los beneficios combinan 2 cosechas de lotes distintos
    de la misma finca (ejercita las pivotes y la ponderación de features).

### 3.3 Reglas agronómicas: funciones de respuesta y mecanismos por target

Principios de diseño (incorporan la revisión metodológica externa):

- **Funciones de respuesta, no pesos lineales.** Cada factor aporta mediante
  una función explícita (por tramos o paramétrica simple): curvas con zona
  óptima, saturación o rendimiento decreciente según el caso. Ningún efecto
  es un salto binario ni un coeficiente lineal plano.
- **Mecanismos propios por target.** Los cuatro targets **no** son
  transformaciones de una única variable latente: comparten componentes donde
  la agronomía lo indica, pero cada uno tiene su mecanismo, para que el
  problema de aprendizaje no sea artificialmente fácil ni circular.
- **Interacciones explícitas**: sombra × temperatura, variedad × roya,
  altitud → temperatura (acople físico con ruido), lluvia × secado,
  fermentación × temperatura.
- **Heterogeneidad**: ruido por finca y por año, colas de error de manejo,
  faltantes realistas — el generador evita producir una fórmula lineal limpia
  que el modelo pueda recuperar trivialmente.

#### Mecanismos por target

| Target | Mecanismo generativo | Componentes |
|---|---|---|
| `score` (SCA 0–100) | `68 + 22 · g(q_s) + ε_s`, con `g` suavemente no lineal | `q_s` (calidad sensorial latente): base varietal + curva de altitud + curva de edad + sombra×temperatura + lluvia en llenado (zona óptima) + nutrición (zona óptima) + % verdes + fermentación (ventana móvil) + demora al despulpado + secado. |
| `defects_pct` | Mecanismo propio: `d_base(q_s·w) + d_broca(bored_pct) + d_verdes(green_pct) + d_secado + ε_d` | La broca aporta **directamente** (grano brocado es defecto físico: relación casi lineal, §abajo); los verdes aportan inmaduros; el sobresecado aporta quebrados. Solo una fracción menor viene de `q_s`. |
| `yield_factor` | Mecanismo físico independiente de `q_s`: `92 + y_broca + y_roya·susc(variedad) + y_vaneo(déficit hídrico) − y_densidad(altitud) + ε_y` | **Definición (término estándar de la industria): kg de pergamino seco necesarios para obtener 70 kg de excelso. Menor = mejor.** Rango típico 88–105. El nombre y la semántica se conservan porque son los del gremio (no se renombra a "loss"). |
| `humidity_pct` | **Solo proceso de secado** — independiente de `q_s`: función de días, método, lluvia del periodo y punto de recogida + `ε_h` | Sirve de *sanity check* de esa ruta del pipeline (§7.4). |

#### Funciones de respuesta (formas; parámetros exactos en `rules.py`)

| Factor | Forma funcional | Dirección (respaldada por fuente) |
|---|---|---|
| Variedad | Dos atributos independientes por variedad: `base_taza` y `susceptibilidad_roya` (Castillo: taza media, resistencia alta; Caturra: taza media, susceptible; Geisha/Bourbon: taza alta) | El perfil varietal existe; su expresión depende de ambiente y manejo (por eso es solo la base, no un ranking determinante). |
| Altitud | Curva de rendimiento decreciente con óptimo amplio (~1.500–1.900 m), no umbral | Mayor altitud → grano más denso y ácido, con saturación. |
| Edad efectiva | Curva por tramos: sube hasta ~4, meseta 4–8, decae > 12 sin zoca | Ciclo productivo del cafeto. |
| Sombra | Interacción: benéfica en zonas bajas/calientes, ~neutra en altura fría | Regulación térmica del sombrío. |
| Lluvia en llenado | Zona óptima (déficit → grano vano; exceso → fermentos y roya) | Ni "más es mejor" ni "menos es mejor". |
| Nutrición | Zona óptima respecto a lo recomendado: insuficiente → −, adecuada → +, exceso → beneficio marginal decreciente (no neutro) | Respuesta a fertilización con saturación. |
| Broca (cadena: infestación en campo → % brocado en cosecha → targets) | **Forma distinta por target.** Sobre `score`: **sigmoide** con tres zonas — plana a baja infestación (la selección de flotes en beneficio y la trilla absorben el grano dañado), aceleración al superarse esa capacidad de filtrado, y meseta en el extremo por efecto piso (el café ya salió de grado). Sobre `defects_pct`: casi lineal con leve aceleración, porque el daño es físico y directo (fruto perforado → grano dañado). | Daño por *Hypothenemus hampei*. ⚠️ La **inflexión de calidad** (parámetro de simulación, ≈ 4 %) es una cantidad **distinta** del **umbral económico de acción** del MIB (2 %, el default de `broca_alert_pct`): el primero marca dónde se dispara el daño a la taza, el segundo dónde el control se paga solo. No deben alinearse por comodidad. |
| Roya % | Efecto sobre `yield_factor` **multiplicado por susceptibilidad varietal** | Debilitamiento del árbol; resistencia genética documentada. |
| % verdes | Curva creciente convexa sobre defectos y score | Inmaduros → astringencia y defecto físico. La magnitud relativa asignada es **decisión de simulación** documentada como tal. |
| Demora cosecha→despulpado | Penalización progresiva y continua desde ~6 h, acelerando después de ~12 h (no un salto en 12 h) | Inicio de fermentación indeseada. |
| Horas de fermentación | Ventana óptima **móvil**: centro ≈ 12–18 h a 20 °C, se acorta con temperatura ambiente mayor; corto → leve, largo → penalización fuerte | Sobrefermentación (vinagre). |
| Secado | Función conjunta de método, días, temperatura y lluvia; muy rápido → **sobresecado** (humedad < 10 %: grano quebradizo, pérdida de peso y taza plana); muy lento + lluvia → riesgo de moho/fermento | Se usa el término "sobresecado" (no "cristalizado", jerga sin definición técnica). |

#### Unidades canónicas

Todas las magnitudes del generador, `rules.py` y `features.py` usan estas
unidades — sin excepciones ni conversiones implícitas:

`altitud` m s.n.m. · `temperatura` °C · `lluvia` mm · `humedad` % ·
`broca/roya/verdes/defectos` % (0–100) · `fermentación` horas ·
`demora al despulpado` horas · `secado` días · `pesos` kg ·
`edad` años · `score` puntos SCA (0–100) · `yield_factor` kg/70 kg excelso.

#### Agregación en mezclas

Ponderación por kg aportados (misma lógica que la trazabilidad — es un
requisito de consistencia del pipeline), **con la agregación definida por
variable**: promedios ponderados para propiedades composicionales (humedad,
% de defectos, % verdes); para `score` el promedio ponderado se adopta como
aproximación declarada (la mezcla sensorial real no es perfectamente aditiva);
los factores de lote/ciclo (edad, altitud, manejo) entran ponderados a los
mecanismos, no promediando el resultado.

### 3.4 Distribuciones de entrada

Ninguna variable se genera uniforme entre mínimo y máximo. Cada una tiene una
distribución plausible definida en `rules.py` (normal truncada, lognormal o
categórica con pesos): altitudes concentradas en 1.400–1.800, fermentaciones
alrededor de la ventana con colas, broca mayormente baja con brotes, etc.
Los rangos físicos admisibles de cada variable se declaran **antes** de
generar y la capa de validación (§3.6) los verifica después.

**Requisito de masa en las zonas informativas.** La forma de una función de
respuesta y la distribución de su variable son **una sola decisión**: una
sigmoide con inflexión en ~4 % de broca es inaprendible si el 95 % de los
secados cae en la zona plana — el modelo no vería nunca la aceleración y las
curvas de dependencia parcial saldrían ruidosas justo donde importa. Por eso
las distribuciones de las variables con umbral (broca, fermentación fuera de
ventana, humedad final, demora al despulpado) se calibran para dejar una
**cola suficiente por encima del punto de inflexión** — realista, porque las
fincas descuidadas y los años de brote existen, pero deliberadamente no
marginal. La validación (§3.7) verifica el % de muestras en cada zona.

### 3.5 Ruido

- Cada target tiene su ruido propio `ε ~ N(0, σ²)` con σ **documentada en
  `rules.py`** y justificada (la variabilidad sensorial de `score` no es la
  de una medición de humedad): valores iniciales `σ_score = 1.5` puntos,
  `σ_defects = 1.2` pp, `σ_yield = 2.0` kg, `σ_humidity = 0.3` pp.
- **El ruido se calibra para que los valores fuera de rango físico sean
  rarísimos** (< 0,1 %); el clipping a límites físicos existe como última
  defensa pero no puede deformar la distribución (se reporta cuántos valores
  recortó — si supera el umbral, la calibración está mal).
- También hay ruido de proceso aguas arriba (clima por finca/año, colas de
  manejo), para que la relación features→target no sea recuperable como una
  fórmula cerrada.

### 3.6 Datos faltantes (realismo de captura)

Nivel `realistic` (por probabilidad de que el farmer NO registre):

| Grupo | % faltante | Racional |
|---|---|---|
| Análisis de suelo | 70 % | Pocos hacen análisis de laboratorio. |
| Clima diario | 50 % | Registro manual intermitente (se simula registrando solo algunos días). |
| Monitoreos de plagas | 40 % | |
| Floración | 40 % | |
| Riegos / labores culturales | 30 % | |
| Fertilizaciones | 15 % | Es la labor que más se registra (cuesta plata). |
| Calidad en cereza | 25 % | |
| Beneficio/secado (fechas, kg) | 5 % | Datos mínimos de trazabilidad, casi siempre presentes. |

El faltante se aplica **sobre el registro, no sobre la simulación**: el mundo
sintético siempre tiene clima y broca; lo que falta es su registro — igual
que la realidad. `--missing-level none` genera el dataset completo (para
medir cuánta precisión cuesta el faltante, §7.6).

### 3.7 Validación del generador y artefacto de auditoría

Tras generar, el propio script ejecuta una **validación automática** y aborta
con reporte si algo falla:

- Rangos físicos y tipos de todas las columnas (según §3.3 unidades).
- Balance de masas en toda la cadena (cereza ≥ flotes + lavado; Σ pivotes).
- Fechas encadenadas (floración < cosecha < despulpado < secado).
- % de faltantes efectivo ≈ el configurado.
- Correlaciones esperadas presentes pero no perfectas (ej. altitud–temperatura
  negativa fuerte pero < |1|).
- Conteo de valores recortados por límites físicos < 0,1 %.
- **Masa por zona en variables con umbral** (§3.4): % de secados por debajo,
  dentro y por encima del punto de inflexión de broca, fermentación, humedad
  y demora al despulpado. Si alguna zona informativa queda por debajo del
  mínimo configurado, el generador advierte: el dataset no permitirá aprender
  esa parte de la curva.

Además escribe un **artefacto de auditoría** (parquet en
`scripts/farm_ml/output/`, fuera de la DB): por cada secado, las variables
latentes usadas (`q_s`, componentes por factor, nivel de manejo de la finca,
ruidos sorteados). Permite auditar por qué un registro recibió su target.
**Las latentes jamás entran como features** — en la realidad no existirían.

## 4. Extracción de features (`ml/features.py`)

Una única función `build_features(drying_id | plot_id_activo, as_of_date)`
usada por **entrenamiento e inferencia** (misma query, cero divergencia).

**Reglas anti-fuga (data leakage):**

1. Toda feature se calcula **solo con datos fechados ≤ `as_of_date`**
   (en entrenamiento, la fecha de cierre del secado; en inferencia, hoy).
2. Ninguna feature deriva directa ni indirectamente de los targets
   (`quality_evals` etapa `parchment` está vetada como fuente de features).
3. Las features se clasifican por **etapa de disponibilidad** — pre-cosecha
   (lote, suelo, clima, labores, sanidad, floración), cosecha (composición
   cereza, kg), proceso (beneficio, secado) — y la proyección sobre un ciclo
   activo solo usa las etapas ya ocurridas (las futuras se imputan, abajo).

Vector de features (agregaciones sobre el/los ciclos que alimentan el secado,
ponderadas por kg en mezclas):

| Feature | Tipo | Etapa | Fuente |
|---|---|---|---|
| variety | categórica | pre | plots |
| altitude | numérica | pre | farms |
| effective_age_years | numérica | pre | plots + plot_events (zoca) |
| shade_type, soil_type | categóricas | pre | plots |
| density_trees_ha | numérica | pre | plots (calculada de distancias) |
| soil_ph, soil_om_pct | numéricas | pre | último soil_analysis ≤ fecha |
| rain_mm_cycle, rain_mm_pre_harvest_90d | numéricas | pre | climate_records por rango |
| temp_avg_cycle | numérica | pre | climate_records |
| n_fertilizations, fert_kg_total | numéricas | pre | fertilizations |
| days_since_last_fert | numérica | pre | fertilizations |
| n_phyto_apps | numérica | pre | phytosanitary_apps |
| broca_pct_last, roya_pct_last | numéricas | pre | pest_monitorings |
| n_weedings, n_prunings | numéricas | pre | cultural_practices |
| days_flowering_to_harvest | numérica | cosecha | flowering_records + harvests |
| pass_number, cherry_kg | numéricas | cosecha | harvests |
| ripe_pct, green_pct, bored_pct | numéricas | cosecha | quality_evals (cherry) |
| floats_pct | numérica | proceso | wet_processings (floats/entrada) |
| hours_harvest_to_pulp | numérica | proceso | wet_processings vs harvest_works |
| fermentation_hours, fermentation_method | num. + cat. | proceso | wet_processings |
| drying_method | categórica | proceso | dryings |
| drying_days | numérica | proceso | dryings |

En **inferencia sobre ciclo activo** las features de etapas aún no ocurridas
se imputan con la **mediana histórica de la misma finca** (o global si no hay
historia) y se reporta el campo `completeness` (% de grupos de features
presentes) en la respuesta del endpoint.

## 5. Entrenamiento (`scripts/farm_ml/train.py`)

| Aspecto | Decisión | Racional |
|---|---|---|
| Modelo | **`HistGradientBoostingRegressor`** (sklearn), uno por target (4 modelos en un solo artefacto) | Estado del arte tabular en datasets chicos, **maneja `NaN` nativamente** (crítico: §3.6 sin imputar en entrenamiento), rápido, sin GPU. Los árboles capturan las no linealidades e interacciones de §3.3 sin ingeniería manual. |
| Baselines | `DummyRegressor` (media) y regresión lineal | Toda métrica se reporta contra baseline — sin eso, un MAE no dice nada. La lineal además revela cuánta señal es no lineal. |
| Categóricas | `OrdinalEncoder` + soporte categórico nativo del GBM | Evita explosión one-hot. |
| Validación | **`GroupKFold` agrupado por finca** (5 folds) | Evita fuga: dos secados de la misma finca comparten altitud/manejo; separarlos entre train y test inflaría las métricas. |
| Métricas | MAE, RMSE y R² por target + comparación vs baseline | En unidades reales (puntos SCA, pp, kg). |
| Interpretabilidad | Importancias por permutación + dependencia parcial por target | Insumo de los chequeos de coherencia (§7). |
| Artefacto | `ml/artifacts/quality_model_vN.joblib` | Bundle: `{models, feature_names, encoders, metrics, farm_medians, rules_version, generator_seed, trained_at}` — la tupla `rules_version + seed` identifica exactamente el dataset que produjo el modelo. |

## 6. Serving (`ml/predictor.py` + endpoint)

- Singleton que carga `latest` al primer uso (lazy, no en el arranque de la
  API); `predict(features) → {score, defects_pct, yield_factor, humidity_pct}`.
- Endpoint (ya especificado): `GET /farm/plots/{id}/quality-projection` →
  predicción + `completeness` + `model_version` + descargo ("estimación basada
  en modelo entrenado con datos sintéticos").
- Sin reentrenamiento en request, jamás. Reentrenar = correr `train.py` y
  reiniciar (o endpoint admin de `reload` si se quiere en caliente — no en v1).

## 7. Validación del pipeline (reporte de `evaluate.py`)

Distingue dos preguntas: **¿predice bien?** (1, 6) y **¿aprendió relaciones
plausibles?** (2, 3) — ambas se miden.

1. **Métricas vs baseline**: el GBM debe superar claramente a la media y a la
   lineal en los 4 targets (existencia de señal aprendible y no lineal).
2. **Recuperación de reglas**: las importancias de permutación deben rankear
   los factores de forma consistente con los pesos del generador (verdes,
   fermentación y broca en el top para `score`).
3. **Chequeos direccionales y de forma**: sobre las curvas de dependencia
   parcial se verifica el **signo** de cada relación conocida —
   ↑broca → ↓score y ↑defectos; ↑verdes → ↓score; ↑roya → ↑yield_factor
   (peor) con pendiente mayor en variedades susceptibles; fermentación fuera
   de ventana → ↓score. Y donde el generador definió un **umbral**, se
   verifica que la curva aprendida tenga su mayor pendiente en la zona de
   inflexión (broca ≈ 4 %), no una pendiente uniforme: es la prueba de que el
   modelo capturó la no linealidad y no solo la dirección. Los árboles del GBM
   son idóneos para esto (particionan por umbrales), así que un fallo aquí
   apunta a falta de masa en la zona (§3.4) o a bug de extracción, no a
   incapacidad del algoritmo. Un modelo con buen MAE pero signos o formas
   incoherentes **falla** la validación.
4. **Sanity check `humidity_pct`**: R² alto (su mecanismo es casi
   determinista). Valida específicamente la ruta secado → features → target;
   **no** certifica el pipeline completo — para eso están los puntos 1–3 y 5.
5. **Tests de consistencia de `features.py`** (independientes del modelo,
   en `backend/tests/farm_ml/`): sobre una mini-DB fixture con valores
   conocidos, se verifica que la extracción produce exactamente las columnas,
   unidades, rangos y agregaciones esperadas (casos calculados a mano,
   incluida una mezcla ponderada). Es la respuesta correcta al riesgo de
   "bug compartido entre train y serving" (§2).
6. **Curva de faltantes**: métricas con `--missing-level none` vs `realistic`
   → cuantifica el valor de registrar más (argumento para incentivar el
   registro juicioso del farmer).
7. **Test de humo de serving**: predicción del endpoint == predicción del
   artefacto en local para el mismo secado.

## 8. Estructura de archivos

```
backend/scripts/farm_ml/
    rules.py                 # Reglas parametrizadas (ver abajo). Versionado: RULES_VERSION.
    generate_synthetic.py    # CLI: puebla la DB vía ORM (§3) + validación automática (§3.7)
    train.py                 # CLI: extrae dataset con features.py, entrena, guarda vN
    evaluate.py              # CLI: métricas, coherencia direccional, curva de faltantes → reporte .md
    output/                  # artefactos de auditoría (latentes por secado) — git-ignored

backend/app/farm_operations/ml/
    features.py              # build_features(...) — compartido train/inferencia
    predictor.py             # carga artefacto, predict()
    artifacts/               # quality_model_v1.joblib, ... (git-ignored salvo el usado)

backend/tests/farm_ml/
    test_features.py         # consistencia de extracción sobre fixture (§7.5)
```

**Estructura de cada regla en `rules.py`** — separa explícitamente la
evidencia de la decisión de modelado:

```python
RULES["broca_score"] = Rule(
    direction="bored_pct ↑ → score ↓, con efecto de umbral",     # respaldado
    source=("Cenicafé, daño por Hypothenemus hampei; la selección de "
            "flotes y la trilla remueven parte del grano brocado"),  # por la fuente
    form="sigmoide(x0, k, piso)",                                # forma elegida
    params={"x0": 4.0, "k": 0.8, "piso": -12.0},  # DECISIÓN DE SIMULACIÓN:
    note=("x0 NO es el umbral económico de acción del MIB (2 %, usado en "
          "broca_alert_pct). La fuente respalda que existe un efecto de "
          "umbral y su dirección, no la ubicación ni la pendiente."),
)
```

La fuente respalda la **dirección**; la **magnitud** es siempre una decisión
de simulación documentada como tal. La tabla §3.3 se mantiene desde este
archivo.

Dependencias nuevas en `backend/requirements.txt`: `scikit-learn`, `pandas`,
`pyarrow`, `joblib` (sin GPU, sin frameworks pesados).

## 9. Decisiones de este documento — para tu revisión

| # | Decisión | Alternativa descartada |
|---|---|---|
| G1 | El generador **puebla la DB** vía ORM y el dataset sale por `features.py` | Generar un CSV directo de features: más simple pero no ejercita la extracción real ni deja datos de demo — y el objetivo del proyecto es validar el pipeline completo. |
| G2 | Datos sintéticos bajo un `Farmer` marcado `SYNTHETIC_ML_DATA`, borrables con `--wipe` | Una DB aparte para lo sintético: más aislada, pero duplica infraestructura y pierde los datos de demo en la app. |
| G3 | `HistGradientBoostingRegressor`, un modelo por target | Redes neuronales (overkill tabular, peor con poco dato), multi-output conjunto (targets con escalas y ruidos distintos rinden mejor separados). |
| G4 | Validación `GroupKFold` por **finca** | Split aleatorio: fuga de información entre secados de la misma finca, métricas infladas — indefendible metodológicamente. |
| G5 | Los `NaN` van directo al GBM (soporte nativo); imputación por mediana de finca **solo en inferencia** para etapas futuras | Imputar todo en entrenamiento: borra la señal de "no registrado", que es informativa (fincas descuidadas registran menos y producen peor). |
| G6 | `rules.py` separado, cada regla con `direction/source/form/params` — la dirección citada, la magnitud declarada como decisión de simulación | Reglas embebidas o "citar" magnitudes que la fuente no respalda. |
| G7 | **Funciones de respuesta no lineales + interacciones explícitas** (sombra×temp, variedad×roya, altitud→temp con ruido, fermentación×temp, lluvia×secado) | Pesos lineales aditivos: el ML recuperaría una fórmula lineal trivial — experimento circular sin valor. |
| G8 | **Mecanismos propios por target** (score sensorial, defectos con broca directa, yield físico, humedad solo secado) | Un único `q` latente con 4 transformaciones: targets artificialmente correlacionados, problema irrealmente fácil. |
| G9 | `yield_factor` **conserva nombre y semántica del gremio** (kg pergamino / 70 kg excelso; menor = mejor), definido formalmente en §3.3 | Renombrarlo a "loss_factor": se alejaría del término estándar que usan caficultores y compradores en Colombia. |
| G10 | Latentes del generador (`q_s`, manejo, ruidos) **persistidas en artefacto de auditoría** fuera de la DB; jamás como features | Descartarlas (imposible auditar targets) o guardarlas en la DB (riesgo de fuga hacia features). |
| G11 | **Broca como sigmoide sobre `score`** (plana → aceleración → piso) y **casi lineal sobre `defects_pct`**, encadenada `infestación en campo → bored_pct → targets` | Curva monótona saturante única para ambos targets: ignora que la selección de flotes y la trilla absorben el daño a baja infestación, y contradice el principio de mecanismos propios por target (G8). La inflexión de calidad se mantiene **separada** del umbral económico de acción (2 %) para no fabricar una coincidencia que la literatura no respalda. |
| G12 | **La forma de cada función y la distribución de su variable se deciden juntas**: las variables con umbral llevan cola calibrada por encima del punto de inflexión, verificada en la validación | Definir curvas con umbral sobre variables cuya masa vive toda en la zona plana: el umbral existiría en el generador pero sería inaprendible, y la validación de forma (§7.3) fallaría sin causa real. |

## 10. Fuera de alcance (v1)

- Reentrenamiento automático/programado.
- Intervalos de confianza en la predicción (extensión natural: quantile GBM).
- Recomendaciones prescriptivas ("aplica X") — el sistema proyecta, no receta.
- Evaluación externa con datos reales (§1): queda definida como el paso
  siguiente cuando existan mediciones reales.
