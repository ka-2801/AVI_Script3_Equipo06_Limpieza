# Sprint 3 — Análisis histórico y modelo predictivo de PM10 (estación VAL, 2014–2024)

> **Naturaleza de este paquete.** Es una **reconstrucción reproducible y documentada** del procedimiento que llevó de los datos originales al Excel procesado. **No es el código original recuperado**: el código original no estaba disponible. Lo que sí se comprobó es que este código, ejecutado sobre los datos originales, **regenera las 14 hojas del Excel procesado con diferencias numéricas ≤ 6 × 10⁻¹⁴** (ver sección 3).

---

## 1. Objetivo del proyecto

1. Consolidar y analizar el histórico horario de calidad del aire de la estación **VAL** (SINAICA), 2014–2024.
2. Construir un modelo que prediga la concentración de **PM10 a +1, +2 y +3 horas**.
3. Entregar el procedimiento de forma que cualquier integrante del equipo pueda revisarlo, ejecutarlo y justificarlo.

## 2. Estructura de archivos

| Archivo | Contenido |
|---|---|
| `analisis_historico_modelo_VAL.py` | Pipeline completo (carga → limpieza → estadísticas → features → modelos → Excel → validación). |
| `analisis_historico_modelo_VAL.ipynb` | Mismo procedimiento en 15 secciones ejecutables celda por celda. El código de las funciones es idéntico al del `.py`. |
| `README_Sprint3_VAL.md` | Este documento. |
| `DICCIONARIO_VARIABLES_VAL.xlsx` | Diccionario de variables originales, temporales, estadísticas, lags, cíclicas, objetivos y métricas. |
| `Sprint3_Analisis_Historico_Modelo_VAL.xlsx` | Excel de resultados **regenerado por el script** (14 hojas, misma estructura que la referencia). |

**No incluidos** (se proporcionan por separado): `SINAICA_VAL_2014_2024_limpio.xlsx` (datos originales) y el Excel procesado de referencia original (solo se usa para validar).

Al ejecutar, el script crea la carpeta `salida_VAL/` con: el Excel regenerado, `Validacion_reconstruccion_VAL.xlsx` (validación hoja por hoja, sensibilidad, iteraciones del modelo, inspección de los datos de entrada) y `graficas/*.png` (7 gráficas).

## 3. Validación de los resultados (qué se comprobó realmente)

Se ejecutó el script completo sobre los dos archivos adjuntos y se **comparó** (sin copiar valores) cada hoja regenerada contra la referencia.

| Hoja | Filas | Resultado | Máx. diferencia absoluta |
|---|---:|---|---:|
| Resumen | 14 | Idéntica | 0 |
| Historico_horario | 96,432 | Idéntica | 0 |
| Disponibilidad | 11 | Idéntica | 0 |
| Estadisticas_anuales / _mensuales / _horarias / _estacionales | 11 / 132 / 24 / 4 | Idénticas | 5.7 × 10⁻¹⁴ |
| Promedios_diarios | 4,018 | Idéntica | 5.7 × 10⁻¹⁴ |
| Correlaciones | 10 | Idéntica | 5.6 × 10⁻¹⁷ |
| Dataset_modelo_completo | 96,432 | Idéntica | 5.6 × 10⁻¹⁷ |
| Dataset_modelo_utilizable | 62,964 | Idéntica | 5.6 × 10⁻¹⁷ |
| Predicciones_2024 | 7,571 | Idéntica | 5.7 × 10⁻¹⁴ |
| Metricas_modelo | 3 | Idéntica | 3.6 × 10⁻¹⁵ |
| Diccionario_variables | 9 | Idéntica | 0 |

**Métricas recalculadas** (conjunto de prueba 2024) frente a las de referencia:

| Horizonte | N entren. | N prueba | MAE | RMSE | R² | Referencia (MAE / RMSE / R²) |
|---|---:|---:|---:|---:|---:|---|
| +1 hora | 56,070 | 7,540 | 6.404 | 9.592 | 0.813 | 6.404 / 9.592 / 0.813 |
| +2 horas | 55,932 | 7,521 | 9.291 | 13.978 | 0.604 | 9.291 / 13.978 / 0.604 |
| +3 horas | 55,824 | 7,504 | 10.725 | 15.912 | 0.488 | 10.725 / 15.912 / 0.488 |

Las métricas **coinciden con las de referencia porque el procedimiento reconstruido es el mismo**, no porque se hayan copiado: el script nunca lee las métricas de la referencia salvo en la función de validación, que solo compara.

Controles adicionales realizados:

- **Prueba negativa del validador:** se alteraron a propósito una predicción (+0.01), una métrica (+0.001), un dato horario y una cifra del Resumen; el validador detectó las 4 alteraciones. Es decir, la validación no es trivial.
- **Notebook:** se ejecutaron sus 36 celdas de código en orden, sin errores, y la sección 14 reporta 14/14 hojas iguales.
- **Entorno de la prueba:** Python 3.12.3 · scikit-learn 1.9.1 · pandas 3.0.6 · numpy 2.5.4 · matplotlib 3.11.2 · seaborn 0.13.2 · openpyxl 3.1.5. **Solo se probó con estas versiones.** Con otras versiones de scikit-learn pueden aparecer diferencias numéricas pequeñas en las hojas del modelo; el validador usa tolerancia de 10⁻⁶ en esas hojas y lo reportaría.

## 4. Discrepancias, hallazgos y cómo se resolvieron

| # | Hallazgo | Efecto | Decisión |
|---|---|---|---|
| 1 | **La limpieza previa no es reproducible.** El archivo `…_limpio.xlsx` ya es el resultado de una limpieza de los `BD_20xx.xlsx` originales (que no se proporcionaron). Su hoja `Reporte_limpieza` indica, p. ej., que en 2024 se pasó de 114,192 filas a 8,784 (filtro de estación VAL) y que 4 valores fuera de rango se convirtieron en NaN; los umbrales de “fuera de rango” **no están documentados**. | No afecta a lo reconstruido (parte del archivo limpio), pero la cadena completa desde los `BD_20xx` no es verificable. | Se parte del archivo limpio, como hizo la referencia. No se inventó ningún umbral. |
| 2 | `DATE` ya contiene la hora; sumar `HOUR` otra vez duplicaría el desfase. (El propio Excel de referencia lo advierte.) | Evita un error de 0–23 h. | `DATETIME = DATE`. Se verificó que `HOUR` coincide en el 100 % de filas. El código solo suma `HOUR` si `DATE` viniera sin hora. |
| 3 | El Excel de referencia nombra `<VAR>_<lambda_0>` a la columna del percentil 95 (artefacto de pandas). | Solo estético. | Se renombró a `<VAR>_p95`; el validador mapea ambos nombres. Se comprobó numéricamente que equivale a `quantile(0.95)`. |
| 4 | La referencia etiqueta los horizontes “+2 hora” y “+3 hora”. | Solo estético. | Se corrigió el plural (“+2 horas”). La comparación de métricas se hace por posición. |
| 5 | **Early stopping implícito.** `HistGradientBoostingRegressor` activa por defecto `early_stopping='auto'` con más de 10,000 muestras: separa un **10 % aleatorio** del entrenamiento como validación interna (verificado: `validation_score_` existe). Las iteraciones usadas fueron 99, 100 y 100 de un máximo de 100. | No hay fuga de 2024 (solo toca datos ≤ 2023), pero la validación interna es aleatoria y no temporal, y el modelo se ajusta con ≈ 90 % de las filas. Desactivarlo cambia poco: RMSE 9.624 / 14.001 / 15.933 (vs 9.592 / 13.978 / 15.912). | Se **mantuvo el valor por defecto** porque es lo que reproduce la referencia. Queda documentado como limitación. |
| 6 | **Solape en la frontera 2023/2024.** El entrenamiento se define por el año del instante de origen; por tanto, las últimas 1, 2 y 3 horas de 2023 tienen como *objetivo* una medición de 2024 (1, 2 y 3 filas respectivamente). | Fuga marginal. Al excluir esas filas: RMSE 9.606 / 13.985 / 15.915 y R² 0.813 / 0.604 / 0.488 (cambio ≤ 0.014 en RMSE; conclusiones idénticas). | Se **mantuvo la regla de la referencia** para reproducirla y se reporta la sensibilidad (`sensibilidad_frontera`). |
| 7 | **WD en 2015:** el 78 % de las lecturas vale exactamente 0 (media 35.6° vs 132–213° en otros años). Posible valor centinela. | Ninguno en el modelo (WD no se usa). Sí afectaría a análisis de viento. | No se modificó (no se inventan correcciones). Marcado en el diccionario. |
| 8 | Hay 39 valores de PM10 iguales a 0. | Mínimo. | Se tratan como válidos, igual que la referencia. |
| 9 | La tabla `Predicciones_2024` es la **unión** de los tres conjuntos de prueba (7,571 filas) y la columna `PM10_OBSERVADO_ORIGEN` solo proviene del conjunto +1 h; queda vacía en 31 filas. | Hay filas con predicción para +2 h/+3 h pero no +1 h (y viceversa). | Se replicó esa estructura exacta. |
| 10 | Las unidades (µg/m³, ppm, °C, etc.) **no aparecen en ningún archivo**. | Riesgo de citar mal una unidad. | El diccionario las marca como “convención SINAICA, no verificable”. |
| 11 | La especificación original mencionaba las cifras de disponibilidad de PM10 y las métricas como “referencia”. | — | Se recalcularon ambas y coinciden (secciones 3 y 5). |

## 5. Requisitos e instalación

Se espera que funcione con Python 3.10 o superior, pero **solo se probó con Python 3.12.3** y las versiones de la sección 3.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install pandas numpy scikit-learn matplotlib seaborn openpyxl jupyter
```

## 6. Cómo ejecutar

**Script (`.py`).** Coloque los dos Excel en la misma carpeta que el script y ejecute:

```bash
python analisis_historico_modelo_VAL.py
```

Con rutas propias (el segundo archivo es opcional; si no existe, se omite la validación):

```bash
python analisis_historico_modelo_VAL.py \
    --entrada datos/SINAICA_VAL_2014_2024_limpio.xlsx \
    --referencia datos/Sprint3_Analisis_Historico_Modelo_VAL.xlsx \
    --salida resultados
```

Código de salida: `0` correcto · `1` alguna hoja no coincide con la referencia · `2` error de entrada (archivo o columnas faltantes). Tarda aproximadamente de 1 a 3 minutos (la escritura del Excel de 96 mil filas es la parte más lenta).

**Notebook (`.ipynb`).**

```bash
jupyter notebook analisis_historico_modelo_VAL.ipynb
```

Ajuste las rutas en la sección 2 si fuera necesario y ejecute celda por celda (o *Run All*). El notebook se entrega **sin salidas pregrabadas**; al ejecutarlo mostrará tablas y gráficas.

## 7. Pipeline reconstruido

| Paso | Qué ocurre | Verificado contra |
|---|---|---|
| Carga | Lee las 11 hojas anuales; ignora `Reporte_limpieza`, `Estadisticas`, `Matriz_*`, `Graficas`; valida columnas. | Hojas y columnas del original |
| Inspección | Filas, duplicados, saltos no horarios, % de nulos por hoja. | `Reporte_limpieza` (0 duplicados, 0 horas faltantes) |
| Limpieza | `DATETIME = DATE`; conversión numérica; elimina duplicados / fechas inválidas. **No imputa.** | `Historico_horario` |
| Consolidación | Orden cronológico + malla horaria completa (96,432 h, sin huecos de fila). | `Historico_horario`, `Disponibilidad` |
| Variables temporales | ANIO, MES, DIA, HORA, DIA_SEMANA (lunes = 0), DIA_ANIO, ESTACION (dic–feb Invierno, mar–may Primavera, jun–ago Verano, sep–nov Otoño). | `Historico_horario` |
| Estadísticas | Anuales (incl. p95), mensuales, horarias, estacionales, promedios diarios, correlaciones de Pearson por pares. | 6 hojas, idénticas |
| Features | Lags 1, 2, 3, 6, 12, 24 h; seno/coseno de hora (÷24) y mes (÷12); DIA_SEMANA. | `Dataset_modelo_completo` |
| Objetivos | `shift(-1)`, `shift(-2)`, `shift(-3)` de PM10. | `Dataset_modelo_completo` |
| Modelos | 3 × `HistGradientBoostingRegressor`; entrena ≤ 2023, prueba 2024. | `Metricas_modelo`, `Predicciones_2024` |
| Baseline | Persistencia: ŷ(t+h) = PM10(t) sobre las mismas filas de prueba. | Columnas `*_BASELINE_PERSISTENCIA` |

## 8. Justificación de PM10 (frente a PM2.5)

Disponibilidad anual verificada contra los archivos (coincide exactamente con la tabla de la especificación):

| Año | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PM10 (%)** | 95.65 | 98.37 | 44.21 | 57.96 | 47.91 | 50.06 | 93.42 | 80.73 | 44.00 | 70.86 | 91.67 |
| PM2.5 (%) | 0.00 | 0.00 | 0.00 | 27.00 | 0.00 | 0.00 | 4.30 | 2.66 | 27.11 | 59.26 | 63.11 |

Disponibilidad global: **PM10 70.44 %**, O3 82.18 %, **PM2.5 16.68 %**.

- PM10 tiene datos en los **11 años**; PM2.5 tiene **0 % en 5 años** (2014, 2015, 2016, 2018, 2019) y menos del 5 % en 2020–2021. Solo en 2023–2024 supera el 59 %.
- Un modelo de PM2.5 contaría con muy pocas secuencias horarias consecutivas para entrenar (necesita 24 h de historia + horizonte sin huecos) y con estaciones del año y años mal representados.
- PM10 permite estudiar patrones diarios, estacionales y anuales con una base mucho más amplia.
- **Matiz honesto:** PM10 tampoco es continuo: 5 años quedan entre 44 % y 58 % de cobertura (2016, 2017, 2018, 2019, 2022), con huecos de hasta 4,439 horas seguidas. Por eso solo 62,964 de las 96,432 horas son utilizables. PM10 es la **mejor opción disponible**, no una serie completa. (Por la correlación PM10–PM2.5 de 0.84, los patrones de PM10 son además una aproximación razonable del comportamiento de partículas finas, pero eso no sustituye un modelo propio de PM2.5 cuando haya más historia.)

## 9. Algoritmo: `HistGradientBoostingRegressor`

**Qué es.** *Gradient boosting* de árboles de decisión: se construye una secuencia de árboles pequeños, cada uno corrige los errores del conjunto anterior. La variante “Hist” discretiza cada variable en hasta 255 intervalos (histogramas), lo que acelera mucho el entrenamiento en tablas de decenas de miles de filas.

**Parámetros de referencia** (reproducidos): `max_iter=100` (100 árboles), `max_leaf_nodes=15` (árboles pequeños, limita sobreajuste), `l2_regularization=1.0` (penaliza pesos grandes en las hojas), `random_state=42` (reproducibilidad). El resto, por defecto (p. ej. `learning_rate=0.1`, early stopping automático; ver discrepancia 5).

**Por qué es razonable** (justificación técnica; los archivos no registran el motivo original de la elección):

- Captura relaciones **no lineales** e interacciones (p. ej. el efecto de la hora depende del mes) sin tener que especificarlas.
- No requiere escalar variables y maneja bien variables de escalas distintas (µg/m³ frente a seno/coseno).
- Es rápida y estable con ≈ 56 mil filas; tres modelos se entrenan en segundos.
- Es un punto de partida sólido y estándar para datos tabulares, y se compara contra una línea base simple.

## 10. Variables de entrada (12)

| # | Variable | Qué representa | Por qué se usa |
|---|---|---|---|
| 1 | `PM10` | Concentración en la hora de origen *t* | Mayor persistencia: el valor actual es el mejor predictor del próximo. |
| 2–4 | `PM10_LAG_1H`, `_2H`, `_3H` | PM10 de hace 1, 2 y 3 h | Dan tendencia inmediata (subiendo/bajando). |
| 5 | `PM10_LAG_6H` | PM10 de hace 6 h | Memoria de corto-medio plazo. |
| 6 | `PM10_LAG_12H` | PM10 de hace 12 h | Contraste día/noche. |
| 7 | `PM10_LAG_24H` | PM10 de hace 24 h | Misma hora del día anterior: ciclo diario. |
| 8–9 | `HORA_SEN`, `HORA_COS` | sen/cos de 2π·hora/24 | Representan la hora de forma circular. |
| 10–11 | `MES_SEN`, `MES_COS` | sen/cos de 2π·mes/12 | Representan el mes de forma circular (estacionalidad anual). |
| 12 | `DIA_SEMANA` | Lunes = 0 … domingo = 6 | Patrón laboral vs. fin de semana (tráfico). |

Variables como O3 y meteorología **no** se incluyeron en este primer modelo (disponibilidad irregular; la hoja `Resumen` lo indica como posible segunda versión).

## 11. Horizontes de predicción y objetivos

Tres modelos **independientes**, uno por horizonte: `PM10_OBJ_1H`, `PM10_OBJ_2H`, `PM10_OBJ_3H`, es decir, PM10 a +1, +2 y +3 h. Cada objetivo es `PM10.shift(-h)` sobre la malla horaria completa, de modo que “+2 h” son siempre 2 horas reales (y no “2 filas”, que serían otra cosa si faltaran horas). Se usan tres horizontes porque: (a) da una **curva de pérdida de habilidad** con el horizonte (R² 0.81 → 0.60 → 0.49); (b) un modelo por horizonte (*direct forecasting*) evita acumular error como pasaría al encadenar predicciones; (c) son horizontes útiles para alertas de corto plazo.

## 12. Estrategia de entrenamiento y prueba

- **Separación temporal, no aleatoria:** entrenamiento = registros con `ANIO <= 2023`; prueba = `ANIO == 2024`. Una división aleatoria mezclaría horas contiguas (muy autocorrelacionadas) entre entrenamiento y prueba y daría métricas optimistas.
- Para cada horizonte se exigen las 12 entradas y el objetivo de **ese** horizonte (por eso N varía: 56,070 / 55,932 / 55,824).
- **Controles anti-fuga en el código** (`assert`): ningún año > 2023 en entrenamiento; ninguna fila de prueba anterior a 2024; el último instante de entrenamiento es anterior al primero de prueba. Las entradas usan solo *t, t-1, …, t-24* y el objetivo es *t+h*.
- Los lags de las primeras horas de 2024 usan valores de 2023: es legítimo, porque en la práctica ese pasado ya se conocería.
- Excepciones menores documentadas: discrepancias 5 y 6.

## 13. Métricas

- **MAE** (error absoluto medio): promedio de |observado − predicho|, en µg/m³. Es el error “típico”.
- **RMSE** (raíz del error cuadrático medio): como el MAE pero **penaliza más los errores grandes** (picos). Siempre ≥ MAE.
- **R²**: fracción de la varianza de PM10 explicada por el modelo. 1 = perfecto; 0 = no mejora a predecir siempre la media; puede ser negativo.
- **Persistencia** (línea base): predecir que “PM10 dentro de h horas = PM10 ahora”. Es el mínimo que un modelo debe superar.

| Horizonte | MAE modelo | MAE persist. | RMSE modelo | RMSE persist. | R² modelo | R² persist. | Mejora RMSE |
|---|---:|---:|---:|---:|---:|---:|---:|
| +1 hora | 6.404 | 7.246 | 9.592 | 10.907 | 0.813 | 0.759 | 12.1 % |
| +2 horas | 9.291 | 11.237 | 13.978 | 16.998 | 0.604 | 0.415 | 17.8 % |
| +3 horas | 10.725 | 13.937 | 15.912 | 20.799 | 0.488 | 0.125 | 23.5 % |

Lectura: el modelo supera a la persistencia en los tres horizontes y la ventaja **crece** con el horizonte. En +1 h la mejora es modesta (la persistencia ya explica 76 % de la varianza), por lo que conviene no sobrevalorar el R² de 0.81.

## 14. Guía rápida para justificar el trabajo ante el equipo

- **¿Por qué PM10?** Es el único contaminante de partículas con datos en los 11 años (70.44 % global frente a 16.68 % de PM2.5, que tiene 5 años en 0 %). Da más secuencias consecutivas para entrenar y validar. Contrapartida: PM10 también tiene huecos (44–58 % en cinco años).
- **¿Qué algoritmo?** `HistGradientBoostingRegressor` (scikit-learn): boosting de árboles pequeños con histogramas; modela no linealidades e interacciones y es rápido.
- **¿Por qué ese algoritmo?** Buen rendimiento en datos tabulares sin necesidad de escalar ni especificar interacciones, regularizable (`max_leaf_nodes`, L2) y estándar como primera versión. No se afirma que sea el óptimo: no se compararon otros modelos.
- **¿Qué son los lags?** Valores del pasado de la misma variable como entradas (PM10 de hace 1, 2, 3, 6, 12 y 24 h). Convierten la serie temporal en una tabla supervisada y le dan al modelo memoria de la dinámica reciente y del ciclo diario.
- **¿Para qué las variables cíclicas?** Hora y mes son circulares: las 23:00 están junto a las 00:00 y diciembre junto a enero. Codificados como números 0–23 o 1–12 el modelo vería una distancia enorme; con seno/coseno la distancia es la correcta.
- **¿Por qué tres horizontes?** Para medir cómo se degrada la predicción al mirar más lejos y cubrir alertas de corto plazo; un modelo directo por horizonte evita acumular error.
- **¿Cómo fue la separación temporal?** Entrenar con ≤ 2023 y probar con 2024, sin mezclar. Simula el uso real (predecir el futuro con el pasado) y evita fuga de información.
- **¿Qué significan MAE, RMSE y R²?** Error absoluto promedio; error que castiga más los picos; y proporción de varianza explicada (ver sección 13).

## 15. Limitaciones

1. **Un solo año de prueba (2024)**, con 91.67 % de cobertura de PM10. Las métricas son una estimación con una sola partición; no hay validación cruzada temporal ni intervalos de confianza.
2. **Cobertura desigual de PM10** y huecos largos (hasta 4,439 h). Solo se usan filas con 24 h de historia completa, lo que puede sesgar el entrenamiento hacia los periodos mejor monitoreados.
3. **Sin meteorología ni otros contaminantes** como entradas; la dispersión de PM10 depende fuertemente del viento, la lluvia y la inversión térmica. La disponibilidad irregular (p. ej. RH 50 % en 2024) fue el motivo de dejarlas fuera.
4. **Capacidad limitada a +3 h** (R² = 0.49): los picos súbitos no se anticipan bien (RMSE muy superior al MAE).
5. **Hiperparámetros no optimizados** (los de referencia) y sin comparar contra otros algoritmos.
6. **Early stopping aleatorio implícito** y **solape marginal** en la frontera 2023/2024 (discrepancias 5 y 6; efecto cuantificado y pequeño).
7. **Limpieza previa no reproducible** y **unidades no verificables** con los archivos (discrepancias 1 y 10); posible valor centinela en WD 2015.
8. **Reproducibilidad numérica** garantizada solo con las versiones de la sección 3; el modelo es determinista con `random_state=42` en esa configuración.
9. El modelo no es de producción: no incluye monitoreo de desviaciones ni reentrenamiento.
